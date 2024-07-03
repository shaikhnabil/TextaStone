import calendar
from django.http import JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.contrib import messages
from .models import *
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import Group
from django.utils import timezone
from datetime import timedelta,datetime

customer_group,created = Group.objects.get_or_create(name = 'customer')
wholesaler_group,created = Group.objects.get_or_create(name = 'wholesaler')




# Create your views here.
def index(request):
    return render(request,'index.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
         login_user = CustomUser.objects.get(email=email)
        except:
            print("Email does not exist")
            

        grp = Group.objects.get(name='customer')
        users_in_group = grp.user_set.all()

        # print("Email:", email)
        # print("Password:", password)
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user) 
            #checks for the user group and redirect user as per their group.
            if login_user in users_in_group:
                return redirect('customer_dashboard')  
            else:
                return redirect('wholesaler_dashboard')  
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login') 
    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'password and confirm password must be same!')
            return redirect('register')
        
        else:
            # Create the user
            try:
                user = CustomUser.objects.create_user(email=email, username=username, phone_no=phone_number, address=address, password=password)
                if role == 'wholesaler':
                    user.groups.add(wholesaler_group)
                if role == 'customer':
                    user.groups.add(customer_group)  
                user.save()
                messages.success(request,'Registration  Successful!')
                return redirect('login') 
            except:
                messages.error(request,'Invalid User')    
            
         
    wholesaler = Group.objects.get(name = 'wholesaler' )
    users_in_group = wholesaler.user_set.all()
    return render(request,'register.html',{'wholesalers' : users_in_group})


def wholesaler(request):

    connected_customers = 0
    connected_customers = UserMerchent.objects.filter(merchent_id=request.user.id,status=UserMerchent.CONFIRMED).count()

    # Get today's date
    today = timezone.now().date()
    # today = date(2024,4,7)

    # Calculate the start and end dates of the current week
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Calculate the start and end dates of the current month
    start_of_month = today.replace(day=1)
    next_month = start_of_month.replace(day=28) + timedelta(days=3)
    end_of_month = next_month - timedelta(days=next_month.day)

    # print(today,"\n",start_of_week,"\n",end_of_week,"\n",start_of_month,"\n",next_month,"\n",end_of_month)

    data_today = fetch_data(today, today, request.user)
    data_week = fetch_data(start_of_week, end_of_week, request.user)
    data_month = fetch_data(start_of_month, end_of_month, request.user)

    total_today = calculate_total(data_today)
    total_week = calculate_total(data_week)
    total_month = calculate_total(data_month)

    weekly_data = []
    for i in range(7):
        day_start = start_of_week + timedelta(days=i)
        # day_end = day_start + timedelta(days=1)
        daily_records = DistributorRecord.objects.filter(
            who_provide=request.user,
            received_date__date=day_start
        )
        daily_total = sum(record.quantity * record.commission for record in daily_records)
        weekly_data.append(daily_total)

    # print(weekly_data)
    monthly_data = []
    customer_data = [] 
    for month in range(1, today.month + 1):
        month_start = today.replace(month=month, day=1)
        month_end = today.replace(month=month, day=calendar.monthrange(today.year, month)[1])
        monthly_records = DistributorRecord.objects.filter(who_provide=request.user, received_date__range=(month_start, month_end))
        monthly_total = sum(record.quantity * record.commission for record in monthly_records)
        monthly_data.append(monthly_total)
        
          # Count the number of confirmed customers associated with the wholesaler for each month
        customers_count = UserMerchent.objects.filter(
            merchent_id=request.user,
            status=UserMerchent.CONFIRMED,
            user_id_id__date_joined__month=month  # Assuming date_joined represents the creation date of the associated user
        ).count()
        customer_data.append(customers_count)
    # print(customer_data)
 
     # Calculate total billing and total sarees for each customer during the current month
    customers_data = {}
    for record in data_month:
        customer_id = record.who_work.id
        customer_name = record.who_work.username
        billing = customers_data.get(customer_id, {'billing': 0, 'sarees': 0})
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
       # total_price = price.price * record.quantity
        net_price = price.price- record.commission
        total_price = record.quantity * net_price
        billing['billing'] += total_price
        billing['sarees'] += record.quantity
        customers_data[customer_id] = {'name': customer_name, 'billing': billing['billing'], 'sarees': billing['sarees']}
   

    context = {
        'daily_total': total_today,
        'weekly_total': total_week,
        'monthly_total': total_month,
        'total_confirmed_customers': connected_customers,
        'weekly_data':weekly_data,
        'monthly_data': monthly_data,
        'customers_data': customers_data.values(),
        'customer_data': customer_data,
    }

    return render(request, 'wholesaler.html', context)



def fetch_data(start_date, end_date, user):
    # Fetch distributor records within the given date range for the specified user
    data = DistributorRecord.objects.filter(received_date__range=[start_date, end_date], who_provide=user)
    return data

def calculate_total(data):
    # Calculate the total amount based on the provided data
    total_day =0
    for record in data:
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        # print(record.quantity, record.commission,price.price, price.price - record.commission)
        record.daily_total = record.quantity * record.commission
        total_day += record.daily_total
    # print(total_day)
    # total = sum((record.quantity * (record.saree.sareedateprice_set.latest('date').price - record.commission)) for record in data)
    return total_day

def saree_distribution(request):
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        received_date = request.POST.get('received_date')
        return_date = request.POST.get('return_date')
        deadline_date = request.POST.get('deadline_date')
        commission = request.POST.get('commission')
        if return_date=="":
            return_date = None

        #validate dates
        if received_date<=deadline_date:
            user = request.user
            who_provide= CustomUser.objects.get(id=user.id)
            who_work_id=request.POST.get('who_work')
            who_work = CustomUser.objects.get(id=who_work_id)
            saree_id = request.POST.get('saree') 
            saree = Saree.objects.get(id=saree_id)
            data = DistributorRecord.objects.create(quantity=quantity,received_date=received_date,return_date=return_date,
                                     deadline_date=deadline_date,commission=commission,who_work=who_work,who_provide=who_provide,saree=saree)
            data.save()
            messages.success(request,'Record added successfully!')
            return redirect('saree_distribution')   
        else:
            messages.error(request, 'Received date must be less than or equal to Return date or Deadline date!')
            return redirect('saree_distribution')   

    user = request.user
    wholesaler = CustomUser.objects.get(id=user.id)
    confirmed_customers = UserMerchent.objects.filter(
        merchent_id=wholesaler,
        status=UserMerchent.CONFIRMED
    ).values_list('user_id', flat=True)

    # Fetching customers who are confirmed and associated with the wholesaler
    who_work_options = CustomUser.objects.filter(
        id__in=confirmed_customers
    )
    # Fetching all saree options
    saree_options = Saree.objects.filter(who_add=user)
    return render(request, 'saree_distribution.html', {'user': user,'who_work_options':who_work_options,'saree_options': saree_options})


def get_saree_price(request):
    if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        saree_id = request.GET.get('saree_id')
        try:
            saree_date_price = SareeDatePrice.objects.filter(saree_id=saree_id).latest('date')
            price = saree_date_price.price
            return JsonResponse({'price': price})
        except SareeDatePrice.DoesNotExist:
            return JsonResponse({'error': 'Saree price not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def view_disributed_sarees(request):
    # Fetch all DistributorRecord instances for the current logged-in user
    user = request.user
    records = DistributorRecord.objects.filter(who_provide=user)
    
    # Iterate through each record and fetch the appropriate price based on the received date
    for record in records:
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        record.price = price.price if price else 0
    
    return render(request, 'view_disributed_sarees.html', {'data': records})

def update_distribute_saree(request,id):
    distribute_saree = DistributorRecord.objects.get(id=id)
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        commission = request.POST.get('commission')
        received_date = request.POST.get('received_date')
        return_date = request.POST.get('return_date')
        if return_date=="":
            return_date = None
        deadline_date = request.POST.get('deadline_date')
        who_provide = CustomUser.objects.get(id=request.POST.get('who_provide'))
        who_work = CustomUser.objects.get(id=request.POST.get('who_work'))
        saree_id = request.POST.get('saree') 
        saree = Saree.objects.get(id=saree_id)
       
        # Update distribute_saree instance
        distribute_saree.quantity = quantity
        distribute_saree.commission = commission
        distribute_saree.received_date = received_date
        distribute_saree.return_date = return_date
        distribute_saree.deadline_date = deadline_date
        distribute_saree.who_provide = who_provide
        distribute_saree.who_work = who_work
        distribute_saree.saree = saree
        distribute_saree.save()
        messages.success(request, "Distribute Saree updated successfully!")
        return redirect('view_disributed_sarees')
    else:
        user = request.user
        wholesaler = CustomUser.objects.get(id=user.id)
        confirmed_customers = UserMerchent.objects.filter(
        merchent_id=wholesaler,
        status=UserMerchent.CONFIRMED).values_list('user_id', flat=True)

    # Fetching customers who are confirmed and associated with the wholesaler
        who_work_options = CustomUser.objects.filter(
        id__in=confirmed_customers)
        saree_options = Saree.objects.filter(who_add=user)
        saree_date_price = SareeDatePrice.objects.filter(saree_id=distribute_saree.saree).latest('date')
        price = saree_date_price.price
        # Render form with Saree data
        return render(request, 'update_distribute_saree.html',{'distribute_saree':distribute_saree,'saree_options':saree_options,'who_work_options':who_work_options,'price':price})


def delete_distribute_saree(request,id):
    distribute_saree = DistributorRecord.objects.get(id=id)
    if request.method == 'POST':
        distribute_saree.delete()
        messages.success(request,"Saree deleted suceesfully")
        return redirect('view_disributed_sarees')
    else:
        messages.error(request,"Saree deletion failed")
        return redirect('view_disributed_sarees')

def saree(request):
    if request.method == 'POST':
        saree_name = request.POST.get('sariname')
        sample_image = request.FILES.get('sample_image')
        design_no = request.POST.get('design_no')
        fieldIndex = request.POST.get('field_index')
        if fieldIndex == None:
            fieldIndex=1
        # Process dynamic material fields
        material_data = {}
        for i in range(1, int(fieldIndex)+1):  # Get values from all dynamic fields
            material_type = request.POST.get(f'field{i}_material_type')
            quantity = request.POST.get(f'field{i}_quantity')
            if material_type and quantity:
                material_data[material_type] = int(quantity)

        # Store image
        if sample_image:
            fs = FileSystemStorage()
            image_path = fs.save(sample_image.name, sample_image)

        # Create Saree object
        saree = Saree.objects.create(
            saree_name=saree_name,
            sample_image=image_path if sample_image else None,
            material=dict(material_data),  # Store material as a JSON string
            design_no=design_no,
            who_add = CustomUser.objects.get(id = request.user.id)
        )
        saree.save()
        messages.success(request,"Saree Added Successfully.")
        return redirect('saree')  # Redirect to list view (replace with your view name)
    sarees = Saree.objects.filter(who_add=request.user)
    saree_material_list = []
    for saree in sarees:
        materials = eval(saree.material)
        saree_material_list.append((saree, materials))
    
        
    return render(request, 'saree.html', {'saree_material_list': saree_material_list})


def update_saree(request, saree_id):
    saree = Saree.objects.get(id=saree_id)
    if request.method == 'POST':
        # Update Saree data
        saree_name = request.POST.get('sariname')
        design_no = request.POST.get('design_no')
        fieldIndex = request.POST.get('field_index')
        # print(fieldIndex)
        if fieldIndex == None:
            fieldIndex=2
        # Update material data
        materials = {}
        for i in range(1, int(fieldIndex)):  # Get values from all dynamic fields
            material_type = request.POST.get(f'field{i}_material_type')
            quantity = request.POST.get(f'field{i}_quantity')
            if material_type and quantity:
                materials[material_type] = int(quantity)
        # print(materials)
        # Handle file upload (sample image)
        sample_image = request.FILES.get('sample_image', None)
        if sample_image:
            fs = FileSystemStorage()
            image_path = fs.save(sample_image.name, sample_image)
            saree.sample_image = image_path
        
        # Update Saree instance
        saree.saree_name = saree_name
        saree.design_no = design_no
        saree.material = dict(materials)
        saree.save()
        messages.success(request, "Saree updated successfully!")
        return redirect('saree')
    else:
        # Render form with Saree data
        materials_dict = eval(saree.material)
        return render(request, 'update_saree.html', {'saree': saree,'materials': materials_dict})

def delete_saree(request, saree_id):
    saree = get_object_or_404(Saree, id=saree_id)
    if request.method == 'POST':
        saree.delete()
        messages.success(request,"Saree deleted suceesfully")
        return redirect('saree')
    else:
        messages.error(request,"Saree deletion failed")
        return redirect('saree')

def logout_view(request):
    logout(request)
    return redirect('login')

    
# def my_customers(request):
#     #finding the group of customers.
#     grp = Group.objects.get(name='customer')
#     users_in_group = grp.user_set.all()
#     return render(request,'my_customers.html',{'users':users_in_group})

def my_customers(request):
    # Find the group of customers.
    grp = Group.objects.get(name='customer')
    wholesaler = request.user  # Assuming the current user is the wholesaler
    user_merchents = UserMerchent.objects.filter(merchent_id=wholesaler, status=UserMerchent.CONFIRMED)
    confirmed_customer_ids = user_merchents.values_list('user_id', flat=True)

    # Filter users in the customer group who are related to the wholesaler
    users_in_group = grp.user_set.filter(id__in=confirmed_customer_ids)
    
    return render(request, 'my_customers.html', {'users': users_in_group})

def edit_profile(request):
    current_user = request.user
    #Get the user details based on id.
    edit_user = CustomUser.objects.get(id=current_user.id)

    # Determine the user group
    if current_user.groups.filter(name='customer').exists():
        dashboard_template = 'customer_dashboard'
    elif current_user.groups.filter(name='wholesaler').exists():
        dashboard_template = 'wholesaler_dashboard'
    else:
        # Handle other user groups or unauthorized access
        return redirect("login")  # Redirect to login page or show error message

    # print(dashboard_template)

    if request.method == 'POST':
        #getting new data.
        edit_user.phone_no=request.POST.get('phone_no')
        edit_user.address=request.POST.get('address')

        #save the updated data.
        try:
            edit_user.save()
            messages.success(request,"Profile Edited Successfully!")
            return redirect(dashboard_template)
        except Exception:
            messages.error(request,"There is some error,Customer not updated!")
            return redirect(dashboard_template)
        
    return render(request,'update_customer.html',{'customer':edit_user})


def delete_customer(request,customer_id):
    try:
        customer=CustomUser.objects.get(id=customer_id)
        customer.delete()
        messages.success(request,"Customer Deleted Successfully!")
        return redirect("my_customers")
    except Exception:
        messages.error(request,"There is some error,Customer not Deleted!")
        return redirect("my_customers")


def customer_requests(request):
    request_users = UserMerchent.objects.filter(status=UserMerchent.REQUESTED)
    # print(request_users)
    data = []
    for i in request_users:
        data.append(CustomUser.objects.get(id = i.user_id.id))

    return render(request,'customer_requests.html',{'request_users' : data})

def request_accepted(request,request_user_id):
    # print(request_user_id)
    user_merchents = UserMerchent.objects.filter(user_id=request_user_id, status=UserMerchent.REQUESTED)
    for user_merchent in user_merchents:
        user_merchent.status = UserMerchent.CONFIRMED
        user_merchent.save()
    Notifications.objects.create(
                    related_user=CustomUser.objects.get(id = request_user_id),
                    description = f"You and {request.user.username} are connected :)"
                )
    # messages.success(request,"Request Accepted!")
    return render(request,'customer_requests.html')

def request_declined(request,request_user_id):

    user_merchents = UserMerchent.objects.filter(user_id=request_user_id, status=UserMerchent.REQUESTED)
    # print(user_merchents)
    for user_merchent in user_merchents:
        user_merchent.status = UserMerchent.DECLINED
        user_merchent.save()
    Notifications.objects.create(
                    related_user=CustomUser.objects.get(id = request_user_id),
                    description = f"{request.user.username} is declined your request"
                )
    # messages.success(request,"Request Declined!")
    return render(request,'customer_requests.html')

# def analytics(request):
#     total_wholesaler = request.objects.get
#     context = {
#         'total_wholesaler': total_wholesaler,
#     }
#     return render(request,'wholesaler.html',{'context':context})

def saree_price(request):
    if request.method == 'POST':
        saree_id = request.POST.get('saree') 
        saree = Saree.objects.get(id=saree_id)
        price = request.POST.get('saree_price')
        date = request.POST.get('date')
        data = SareeDatePrice.objects.create(saree=saree,price=price,date=date)
        data.save()
        messages.success(request,'Price added successfully!')
        return redirect('saree_price')   
    saree_options = Saree.objects.filter(who_add=request.user)
    price_Data = SareeDatePrice.objects.filter(saree__who_add=request.user)
    return render(request, 'saree_price.html',{'price_Data':price_Data,'saree_options':saree_options})    

# def wholesaler_billing(request):
#    # Fetch all DistributorRecord instances
#     records = DistributorRecord.objects.filter(who_provide=request.user).order_by('received_date')
#     # Iterate through each record and fetch the appropriate price based on the received date
#     nettotal=0
#     netcommission=0
#     totalp=0
#     for record in records:
#         price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
#         record.price = price.price if price else 0
#         record.total = record.price * record.quantity
#         record.totalCommission = record.quantity * record.commission
#         netcommission += record.totalCommission
#         record.netprice = record.price - record.commission
#         record.finalprice = record.netprice * record.quantity
#         nettotal += record.finalprice
#         totalp += record.total
       
#     return render(request, 'wholesaler_billing.html', {'data': records,'nettotal':nettotal,'totalCommission':netcommission,"total":totalp})    


def wholesaler_billing(request):
    if request.method == 'POST':
        selected_month = int(request.POST.get('selected_month'))
    else:
        # Default to the current month
        selected_month = datetime.now().month
   
    # Fetch all DistributorRecord instances for the selected month
    records = DistributorRecord.objects.filter(
        who_provide=request.user,
        received_date__month=selected_month
    ).order_by('received_date')

    # Iterate through each record and fetch the appropriate price based on the received date
    nettotal = 0
    netcommission = 0
    totalp = 0
    for record in records:
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        record.price = price.price if price else 0
        record.total = record.price * record.quantity
        record.totalCommission = record.quantity * record.commission
        netcommission += record.totalCommission
        record.netprice = record.price - record.commission
        record.finalprice = record.netprice * record.quantity
        nettotal += record.finalprice
        totalp += record.total

    # Create a list of months for the dropdown
    months = [(month, datetime.strptime(str(month), "%m").strftime("%B")) for month in range(1, 13)]
    return render(request, 'wholesaler_billing.html', {'data': records, 'nettotal': nettotal, 'totalCommission': netcommission, "total": totalp, 'selected_month': selected_month,'months': months})