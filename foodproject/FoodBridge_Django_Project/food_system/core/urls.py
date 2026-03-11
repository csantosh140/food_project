from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

    # Donor
    path('donor/', views.donor_dashboard, name='donor_dashboard'),
    path('donor/donate/', views.add_donation, name='add_donation'),
    path('donor/donations/', views.donor_donations, name='donor_donations'),
    path('donor/donations/<int:pk>/cancel/', views.cancel_donation, name='cancel_donation'),

    # Delivery
    path('delivery/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/available/', views.available_donations, name='available_donations'),
    path('delivery/accept/<int:pk>/', views.accept_delivery, name='accept_delivery'),
    path('delivery/update/<int:pk>/', views.update_delivery_status, name='update_delivery_status'),
    path('delivery/my/', views.my_deliveries, name='my_deliveries'),

    # Receiver
    path('receiver/', views.receiver_dashboard, name='receiver_dashboard'),
    path('receiver/browse/', views.browse_food, name='browse_food'),
    path('receiver/request/<int:pk>/', views.request_food, name='request_food'),
    path('receiver/food-request/', views.create_food_request, name='create_food_request'),
    path('receiver/feedback/<int:pk>/', views.give_feedback, name='give_feedback'),

    # Shared
    path('donation/<int:pk>/', views.donation_detail, name='donation_detail'),
    
    # Location Tracker
    path('tracker/', views.tracker_view, name='tracker'),
    path('tracker/<int:delivery_id>/', views.tracker_view, name='tracker_delivery'),
    path('api/location/', views.get_location, name='get_location'),
    path('api/location/update/', views.update_location, name='update_location'),
]
