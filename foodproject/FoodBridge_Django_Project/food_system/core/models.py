from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('donor', 'Food Donor'),
        ('delivery', 'Delivery Agent'),
        ('receiver', 'Receiver'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    organization_name = models.CharField(max_length=200, blank=True)
    is_available = models.BooleanField(default=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class FoodDonation(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned to Delivery'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    FOOD_TYPE_CHOICES = [
        ('cooked', 'Cooked Food'),
        ('raw', 'Raw Ingredients'),
        ('packaged', 'Packaged Food'),
        ('fruits_vegetables', 'Fruits & Vegetables'),
        ('bakery', 'Bakery Items'),
        ('dairy', 'Dairy Products'),
        ('other', 'Other'),
    ]

    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    title = models.CharField(max_length=200)
    description = models.TextField()
    food_type = models.CharField(max_length=30, choices=FOOD_TYPE_CHOICES)
    quantity = models.CharField(max_length=100)
    serves_people = models.PositiveIntegerField(default=1)
    
    # Food safety & timing
    cooking_time = models.DateTimeField(null=True, blank=True, help_text="When was the food cooked?")
    expiry_time = models.DateTimeField()
    
    pickup_address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    food_image = models.ImageField(upload_to='food/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='received_donations')
    delivery_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='deliveries')

    def is_expired(self):
        return timezone.now() > self.expiry_time
    
    def is_expiring_soon(self):
        """Returns True if food will expire within 2 hours"""
        warning_threshold = timezone.now() + timedelta(hours=2)
        return warning_threshold >= self.expiry_time > timezone.now()
    
    def hours_until_expiry(self):
        """Returns hours until food expires (negative if expired)"""
        if self.expiry_time:
            delta = self.expiry_time - timezone.now()
            return round(delta.total_seconds() / 3600, 1)
        return None
    
    def time_since_cooking(self):
        """Returns hours since food was cooked"""
        if self.cooking_time:
            delta = timezone.now() - self.cooking_time
            return round(delta.total_seconds() / 3600, 1)
        return None
    
    def get_expiry_status(self):
        """Returns expiry status: 'expired', 'expiring_soon', 'fresh', or 'unknown'"""
        if self.is_expired():
            return 'expired'
        elif self.is_expiring_soon():
            return 'expiring_soon'
        elif self.expiry_time:
            return 'fresh'
        return 'unknown'
    
    def should_auto_expire(self):
        """Check if donation should be auto-expired"""
        return self.status in ['available', 'assigned'] and self.is_expired()

    def __str__(self):
        return f"{self.title} by {self.donor.username}"

    class Meta:
        ordering = ['-created_at']


class DeliveryRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    donation = models.OneToOneField(FoodDonation, on_delete=models.CASCADE, related_name='delivery_request')
    delivery_agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Live location tracking
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery for {self.donation.title}"


class FoodRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]

    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_requests')
    people_count = models.PositiveIntegerField()
    food_preference = models.CharField(max_length=200, blank=True)
    location = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    needed_by = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request by {self.receiver.username} for {self.people_count} people"

    class Meta:
        ordering = ['-created_at']


class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_given')
    donation = models.ForeignKey(FoodDonation, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.from_user.username} - {self.rating}★"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}"

