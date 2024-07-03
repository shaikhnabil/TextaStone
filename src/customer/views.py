from django.shortcuts import render,redirect
from django.contrib.auth.models import User,Group
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout,get_user_model
from django.contrib import messages
from src.wholesaler.models import *
from django.contrib.auth.models import Group
from datetime import timedelta,datetime
from django.utils import timezone

def customer(request):
    # Get total connected wholesaler.
    connected_wholesalers = 0
    connected_wholesalers = UserMerchent.objects.filter(user_id=request.user.id,status=UserMerchent.CONFIRMED).count()
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

    # Fetch data for today, the whole week, and the whole month
    data_today = fetch_data(today, today, request.user)
    data_week = fetch_data(start_of_week, end_of_week, request.user)
    data_month = fetch_data(start_of_month, end_of_month, request.user)

    # Calculate totals for today, the whole week, and the whole month
    total_today = calculate_total(data_today)
    total_week = calculate_total(data_week)
    total_month = calculate_total(data_month)

    weekly_data = []

    # Iterate through each day of the week
    for i in range(7):
        day_start = start_of_week + timedelta(days=i)
        daily_records = DistributorRecord.objects.filter(
            who_work=request.user,
            received_date__date=day_start
        )
        daily_total = sum((record.quantity * (record.saree.sareedateprice_set.latest('date').price - record.commission)) for record in daily_records)
        weekly_data.append(daily_total)

    # print(weekly_data)
    
    #calculate monthly data
    current_year = today.year
    data_year = DistributorRecord.objects.filter(
        who_work=request.user,
        received_date__year=current_year
    )
    #month_data = [0] * 12
    # month_data = [0] * today.month
    # for record in data_year:
    #     month_index = record.received_date.month - 1 
    #     price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first().price
    #     month_data[month_index] += record.quantity * (price - record.commission)
        
    month_data = [0] * today.month
    for record in data_year:
        month_index = record.received_date.month - 1 
        price_query = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        if price_query is not None:
            price = price_query.price
            month_data[month_index] += record.quantity * (price - record.commission) 
               
    connection_data = []

    # Iterate over each month of the year
    for month in range(1, today.month+1):
        # Count the number of connected wholesalers for the current month
        wholesalers_count = UserMerchent.objects.filter(
            user_id=request.user.id,
            status=UserMerchent.CONFIRMED,
            merchent_id_id__date_joined__year=current_year,
            merchent_id_id__date_joined__month=month
        ).count()
        
        connection_data.append(wholesalers_count)
     
     # Calculate total billing and total sarees for each wholesaler during the current month
    wholesalers_data = {}
    for record in data_month:
        wholesaler_id = record.who_provide.id
        wholesaler_name = record.who_provide.username
        billing = wholesalers_data.get(wholesaler_id, {'billing': 0, 'sarees': 0})
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        #total_price = price.price * record.quantity
        net_price = price.price- record.commission
        total_price = record.quantity * net_price
        billing['billing'] += total_price
        billing['sarees'] += record.quantity
        wholesalers_data[wholesaler_id] = {'name': wholesaler_name, 'billing': billing['billing'], 'sarees': billing['sarees']}


    context = {'total_today': total_today, 
               'total_week': total_week, 
               'total_month': total_month,
               'wholesalers':connected_wholesalers,
               'week_data':weekly_data,
               'month_data':month_data,
               'connection_data':connection_data,
               'wholesalers_data': wholesalers_data.values(),
               }
    return render(request, 'customer.html',context)

def fetch_data(start_date, end_date, user):
    # Fetch distributor records within the given date range for the specified user
    return DistributorRecord.objects.filter(received_date__range=[start_date, end_date], who_work=user)

def calculate_total(data):
    # Calculate the total amount based on the provided data
    total_day =0
    for record in data:
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        # print(record.quantity, record.commission,price.price, price.price - record.commission)
        #record.daily_total = record.quantity * (price.price - record.commission)
        if price is not None:
            record.daily_total = record.quantity * (price.price - record.commission)
        else:
            record.daily_total = 0  # Set daily_total to 0 as an example
        total_day += record.daily_total
    # print(total_day)
    # total = sum((record.quantity * (record.saree.sareedateprice_set.latest('date').price - record.commission)) for record in data)
    return total_day


def request_wholesaler(request):
    wholesaler_group = Group.objects.get(name='wholesaler')

    # Get the wholesalers in the group
    all_wholesalers = wholesaler_group.user_set.all()
    current_user = request.user

    # Get the IDs of all wholesalers connected with the current user
    connected_wholesaler_ids = UserMerchent.objects.filter(user_id=current_user).values_list('merchent_id', flat=True)

    # Filter out the wholesalers that are not connected with the current user
    available_wholesalers = all_wholesalers.exclude(id__in=connected_wholesaler_ids)

    return render(request, 'request_wholesaler.html', {'wholesalers': available_wholesalers})


CustomUser = get_user_model()

def send_request(request, wholesaler_id):
    user_request = request.user
    # print(user_request)
    try:
        wholesaler = CustomUser.objects.get(id=wholesaler_id)
        # print(wholesaler,wholesaler.id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'There is some error,Request not sent!')
        return redirect('request_wholesaler')

    # Check if there is an existing request from the same customer to the same wholesaler
    existing_request = UserMerchent.objects.filter(
        merchent_id=wholesaler,
        user_id=user_request,
    ).exists()

    if not existing_request:
        # Create a UserMerchent object
        UserMerchent.objects.create(
            merchent_id=wholesaler,
            user_id=user_request,
        )
        messages.success(request, 'Request sent successfully!')
        Notifications.objects.create(
                    related_user=CustomUser.objects.get(id = wholesaler_id),
                    description = f"You have new connection request from {request.user}"
                )
    else:
        messages.error(request, 'You have already sent a request to this wholesaler!')

    # Return the response
    return render(request, 'customer.html')

def notifications(request):
    notifications = Notifications.objects.filter(related_user=request.user)  # Fetch notifications related to the current user
    # print(notifications)
    customer_group = Group.objects.get(name='customer')
    customers = customer_group.user_set.all()
    return render(request, 'notifications.html', {'notifications': notifications,'customers' : customers})

def close_notification (request,notification_id):
    try:
        notification = Notifications.objects.get(id=notification_id)
        notification.delete()
        # Optionally, you can return a success message or redirect to another page
    except Notifications.DoesNotExist:
        messages.error(request,"No notifications!")
    return render(request,'notifications.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def sarees(request):
    # Retrieve UserMerchent instances where the customer is involved and the status is confirmed
    user_merchants = UserMerchent.objects.filter(user_id=request.user, status=UserMerchent.CONFIRMED)
    
    # Get the connected wholesalers from the UserMerchent instances
    connected_wholesalers = [user_merchant.merchent_id for user_merchant in user_merchants]

    # Get the Sarees that is related to this wholesalers.
    sarees = Saree.objects.filter(who_add__in=connected_wholesalers)
    # print(sarees)
    return render(request,'customer_sarees.html',{'sarees' : sarees})   

# def customer_billing(request):
#     # Get the data of requested user
#     records = DistributorRecord.objects.filter(who_work = request.user).order_by('received_date')
#     totalp=0
#     # Iterate over received data.
#     for record in records:
#         # Get price of saree at the provided time.
#         price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
#         record.price = price.price if price else 0
#         record.netprice = record.price- record.commission 
#         record.total = record.quantity * record.netprice
#         totalp += record.total
#     return render(request, 'customer_billing.html',{'data': records,'totalp':totalp}) 

def customer_billing(request):
    if request.method == 'POST':
        selected_month = int(request.POST.get('selected_month'))
    else:
        # Default to the current month
        selected_month = datetime.now().month

    # Fetch all DistributorRecord instances for the selected month
    records = DistributorRecord.objects.filter(
        who_work=request.user,
        received_date__month=selected_month
    ).order_by('received_date')

    totalp = 0

    # Iterate over received data.
    for record in records:
        # Get price of saree at the provided time.
        price = SareeDatePrice.objects.filter(saree=record.saree, date__lte=record.received_date).order_by('-date').first()
        record.price = price.price if price else 0
        record.netprice = record.price - record.commission 
        record.total = record.quantity * record.netprice
        totalp += record.total

    # Create a list of months for the dropdown
    months = [(month, datetime.strptime(str(month), "%m").strftime("%B")) for month in range(1, 13)]

    return render(request, 'customer_billing.html', {'data': records, 'totalp': totalp, 'selected_month': selected_month, 'months': months})