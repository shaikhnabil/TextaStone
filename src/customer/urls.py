from django.contrib import admin
from django.urls import path
from . import views
# from wholesaler import views


urlpatterns = [
    path('customer/',views.customer,name='customer_dashboard'), 
    path('customer/request_wholesaler/',views.request_wholesaler,name='request_wholesaler'),
    path('customer/request_wholesaler/send_request/<int:wholesaler_id>',views.send_request,name='send_request'),
    path('customer/notifications/',views.notifications,name='notifications_customer'),
    path('wholesaler/notifications/',views.notifications,name='notifications_wholesaler'),
    path('logout/',views.logout_view,name='logout_view'),


    # path('customer/notifications/close_notification/<int:notification_id>',views.close_notification,name='close_notification'),
    # path('wholesaler/notifications/close_notification/<int:notification_id>',views.close_notification,name='close_notification'),

     # For customer notifications
    path('customer/notifications/close_notification/<int:notification_id>/', views.close_notification, name='customer_close_notification'),

    # For wholesaler notifications
    path('wholesaler/notifications/close_notification/<int:notification_id>/', views.close_notification, name='wholesaler_close_notification'),
    
    path('customer/customer_billing/',views.customer_billing,name='customer_billing'),
   

    path('customer/sarees/',views.sarees,name='sarees'),

]