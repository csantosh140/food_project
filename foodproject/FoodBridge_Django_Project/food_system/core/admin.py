from django.contrib import admin
from .models import UserProfile, FoodDonation, DeliveryRequest, FoodRequest, Feedback, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'city', 'phone', 'created_at']
    list_filter = ['role', 'city']
    search_fields = ['user__username', 'user__email', 'city']

@admin.register(FoodDonation)
class FoodDonationAdmin(admin.ModelAdmin):
    list_display = ['title', 'donor', 'food_type', 'serves_people', 'status', 'city', 'created_at']
    list_filter = ['status', 'food_type', 'city']
    search_fields = ['title', 'donor__username', 'city']

@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    list_display = ['donation', 'delivery_agent', 'status', 'created_at']
    list_filter = ['status']

@admin.register(FoodRequest)
class FoodRequestAdmin(admin.ModelAdmin):
    list_display = ['receiver', 'people_count', 'city', 'status', 'created_at']
    list_filter = ['status', 'city']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'donation', 'rating', 'created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read']
