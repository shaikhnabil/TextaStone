from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('index',views.index,name='index'),
    path('',views.login,name='login'),
    path('register/',views.register,name='register'),  
    path('wholesaler/',views.wholesaler,name='wholesaler_dashboard'),   
    path('wholesaler/saree/',views.saree,name='saree'),
    path('wholesaler/saree_price/',views.saree_price,name='saree_price'),
    path('wholesaler/saree/update_saree/<int:saree_id>/', views.update_saree, name='update_saree'),
    path('wholesaler/saree/delete_saree/<int:saree_id>/', views.delete_saree, name='delete_saree'),
    path('wholesaler/saree_distribution/',views.saree_distribution,name='saree_distribution'),   
    path('wholesaler/view_disributed_sarees/',views.view_disributed_sarees,name='view_disributed_sarees'),   
    path('get_saree_price/', views.get_saree_price, name='get_saree_price'),
    path('wholesaler/view_disributed_sarees/update_distribute_saree/<int:id>/', views.update_distribute_saree, name='update_distribute_saree'),
    path('wholesaler/view_disributed_sarees/delete_distribute_saree/<int:id>/', views.delete_distribute_saree, name='delete_distribute_saree'),
    path('wholesaler/my_customers/', views.my_customers, name='my_customers'),    
    # path('wholesaler/my_customers/update_customer/<int:customer_id>', views.update_customer, name='edit_profile'),  
      
    path('wholesaler/edit_profile', views.edit_profile, name='edit_profile_wholesaler'),
    path('customer/edit_profile', views.edit_profile, name='edit_profile_customer'),

    path('wholesaler/my_customers/delete_customer/<int:customer_id>', views.delete_customer, name='delete_customer'),    
    path('wholesaler/my_customers/customer_requests', views.customer_requests, name='customer_requests'),  
    path('wholesaler/my_customers/customer_requests/<int:request_user_id>/accept', views.request_accepted, name='request_accepted'),  
    path('wholesaler/my_customers/customer_requests/<int:request_user_id>/decline', views.request_declined, name='request_declined'), 
    path('wholesaler/wholesaler_billing/',views.wholesaler_billing,name='wholesaler_billing'),
    path('logout_view/',views.logout_view,name='logout_view'),  
]