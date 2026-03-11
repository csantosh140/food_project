import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import UserProfile, FoodDonation, DeliveryRequest, FoodRequest, Feedback, Notification
from .forms import RegisterForm, FoodDonationForm, FoodRequestForm, FeedbackForm, ProfileUpdateForm


def notify(user, message):
    Notification.objects.create(user=user, message=message)


# ─── AUTH VIEWS ───────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    stats = {
        'total_donations': FoodDonation.objects.count(),
        'delivered': FoodDonation.objects.filter(status='delivered').count(),
        'donors': UserProfile.objects.filter(role='donor').count(),
        'receivers': UserProfile.objects.filter(role='receiver').count(),
    }
    return render(request, 'core/home.html', {'stats': stats})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    profile = request.user.profile
    if profile.role == 'donor':
        return redirect('donor_dashboard')
    elif profile.role == 'delivery':
        return redirect('delivery_dashboard')
    elif profile.role == 'receiver':
        return redirect('receiver_dashboard')
    return redirect('home')


# ─── DONOR VIEWS ──────────────────────────────────────────────────────────────

@login_required
def donor_dashboard(request):
    if request.user.profile.role != 'donor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    donations = FoodDonation.objects.filter(donor=request.user)
    stats = {
        'total': donations.count(),
        'available': donations.filter(status='available').count(),
        'delivered': donations.filter(status='delivered').count(),
        'in_transit': donations.filter(status__in=['assigned', 'in_transit']).count(),
        'total_served': sum(d.serves_people for d in donations.filter(status='delivered')),
    }
    recent = donations[:5]
    notifications = request.user.notifications.filter(is_read=False)[:5]
    return render(request, 'core/donor_dashboard.html', {
        'stats': stats, 'recent_donations': recent, 'notifications': notifications
    })


@login_required
def add_donation(request):
    if request.user.profile.role != 'donor':
        return redirect('dashboard')
    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.save()
            messages.success(request, 'Food donation listed successfully!')
            # Notify delivery agents
            for agent in UserProfile.objects.filter(role='delivery', is_available=True):
                notify(agent.user, f'New food donation available: {donation.title} in {donation.city}')
            return redirect('donor_dashboard')
    else:
        form = FoodDonationForm()
    return render(request, 'core/add_donation.html', {'form': form})


@login_required
def donor_donations(request):
    if request.user.profile.role != 'donor':
        return redirect('dashboard')
    donations = FoodDonation.objects.filter(donor=request.user)
    return render(request, 'core/donor_donations.html', {'donations': donations})


@login_required
def cancel_donation(request, pk):
    donation = get_object_or_404(FoodDonation, pk=pk, donor=request.user)
    if donation.status in ['available', 'assigned']:
        donation.status = 'cancelled'
        donation.save()
        messages.success(request, 'Donation cancelled.')
    return redirect('donor_donations')


# ─── DELIVERY VIEWS ───────────────────────────────────────────────────────────

@login_required
def delivery_dashboard(request):
    if request.user.profile.role != 'delivery':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    my_deliveries = DeliveryRequest.objects.filter(delivery_agent=request.user)
    available_donations = FoodDonation.objects.filter(status='available').exclude(
        delivery_request__isnull=False
    )
    stats = {
        'total': my_deliveries.count(),
        'completed': my_deliveries.filter(status='delivered').count(),
        'active': my_deliveries.filter(status__in=['accepted', 'picked_up']).count(),
        'available_to_pick': available_donations.count(),
    }
    active_deliveries = my_deliveries.filter(status__in=['accepted', 'picked_up'])
    notifications = request.user.notifications.filter(is_read=False)[:5]
    return render(request, 'core/delivery_dashboard.html', {
        'stats': stats, 'active_deliveries': active_deliveries,
        'available_donations': available_donations[:6], 'notifications': notifications
    })


@login_required
def available_donations(request):
    if request.user.profile.role != 'delivery':
        return redirect('dashboard')
    donations = FoodDonation.objects.filter(status='available')
    city_filter = request.GET.get('city', '')
    if city_filter:
        donations = donations.filter(city__icontains=city_filter)
    return render(request, 'core/available_donations.html', {'donations': donations, 'city_filter': city_filter})


@login_required
def accept_delivery(request, pk):
    if request.user.profile.role != 'delivery':
        return redirect('dashboard')
    donation = get_object_or_404(FoodDonation, pk=pk, status='available')
    # Check if already taken
    if DeliveryRequest.objects.filter(donation=donation).exists():
        messages.error(request, 'This donation has already been assigned.')
        return redirect('available_donations')
    dr = DeliveryRequest.objects.create(
        donation=donation,
        delivery_agent=request.user,
        status='accepted',
        accepted_at=timezone.now()
    )
    donation.status = 'assigned'
    donation.delivery_agent = request.user
    donation.save()
    notify(donation.donor, f'Your donation "{donation.title}" has been accepted by a delivery agent.')
    messages.success(request, 'Delivery accepted! Please pick up the food.')
    return redirect('delivery_dashboard')


@login_required
def update_delivery_status(request, pk):
    if request.user.profile.role != 'delivery':
        return redirect('dashboard')
    dr = get_object_or_404(DeliveryRequest, pk=pk, delivery_agent=request.user)
    new_status = request.POST.get('status')
    if new_status == 'picked_up' and dr.status == 'accepted':
        dr.status = 'picked_up'
        dr.picked_up_at = timezone.now()
        dr.donation.status = 'in_transit'
        dr.donation.save()
    elif new_status == 'delivered' and dr.status == 'picked_up':
        dr.status = 'delivered'
        dr.delivered_at = timezone.now()
        dr.donation.status = 'delivered'
        dr.donation.save()
        notify(dr.donation.donor, f'Your donation "{dr.donation.title}" has been successfully delivered!')
        if dr.donation.receiver:
            notify(dr.donation.receiver, f'Food donation "{dr.donation.title}" has been delivered to you.')
    dr.save()
    messages.success(request, f'Status updated to {new_status.replace("_", " ").title()}.')
    return redirect('delivery_dashboard')


@login_required
def my_deliveries(request):
    if request.user.profile.role != 'delivery':
        return redirect('dashboard')
    deliveries = DeliveryRequest.objects.filter(delivery_agent=request.user)
    return render(request, 'core/my_deliveries.html', {'deliveries': deliveries})


# ─── RECEIVER VIEWS ───────────────────────────────────────────────────────────

@login_required
def receiver_dashboard(request):
    if request.user.profile.role != 'receiver':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    available_food = FoodDonation.objects.filter(status='available')
    my_requests = FoodRequest.objects.filter(receiver=request.user)
    my_received = FoodDonation.objects.filter(receiver=request.user)
    stats = {
        'available_food': available_food.count(),
        'my_requests': my_requests.count(),
        'fulfilled': my_requests.filter(status='fulfilled').count(),
        'received': my_received.filter(status='delivered').count(),
    }
    notifications = request.user.notifications.filter(is_read=False)[:5]
    return render(request, 'core/receiver_dashboard.html', {
        'stats': stats, 'available_food': available_food[:6],
        'my_requests': my_requests[:5], 'notifications': notifications
    })


@login_required
def browse_food(request):
    if request.user.profile.role != 'receiver':
        return redirect('dashboard')
    donations = FoodDonation.objects.filter(status='available')
    city = request.GET.get('city', '')
    food_type = request.GET.get('food_type', '')
    if city:
        donations = donations.filter(city__icontains=city)
    if food_type:
        donations = donations.filter(food_type=food_type)
    return render(request, 'core/browse_food.html', {
        'donations': donations, 'city': city, 'food_type': food_type,
        'food_types': FoodDonation.FOOD_TYPE_CHOICES
    })


@login_required
def request_food(request, pk):
    if request.user.profile.role != 'receiver':
        return redirect('dashboard')
    donation = get_object_or_404(FoodDonation, pk=pk, status='available')
    donation.receiver = request.user
    donation.save()
    notify(donation.donor, f'{request.user.get_full_name() or request.user.username} has requested your donation "{donation.title}".')
    messages.success(request, f'You have requested "{donation.title}". A delivery agent will be assigned soon.')
    return redirect('receiver_dashboard')


@login_required
def create_food_request(request):
    if request.user.profile.role != 'receiver':
        return redirect('dashboard')
    if request.method == 'POST':
        form = FoodRequestForm(request.POST)
        if form.is_valid():
            fr = form.save(commit=False)
            fr.receiver = request.user
            fr.save()
            messages.success(request, 'Food request submitted successfully!')
            return redirect('receiver_dashboard')
    else:
        form = FoodRequestForm()
    return render(request, 'core/create_food_request.html', {'form': form})


@login_required
def give_feedback(request, pk):
    donation = get_object_or_404(FoodDonation, pk=pk, status='delivered')
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.from_user = request.user
            fb.donation = donation
            fb.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('receiver_dashboard')
    else:
        form = FeedbackForm()
    return render(request, 'core/feedback.html', {'form': form, 'donation': donation})


# ─── SHARED VIEWS ─────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'core/profile.html', {'form': form})


@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def donation_detail(request, pk):
    donation = get_object_or_404(FoodDonation, pk=pk)
    feedbacks = donation.feedbacks.all()
    delivery_req = getattr(donation, 'delivery_request', None)
    return render(request, 'core/donation_detail.html', {
        'donation': donation, 'feedbacks': feedbacks, 'delivery_req': delivery_req
    })


# ─── LOCATION TRACKING API ─────────────────────────────────────────────────────

@login_required
def get_location(request):
    """
    Get the current location of the delivery agent's active delivery.
    Returns JSON with lat, lng, status, speed.
    Can accept delivery_id as GET parameter.
    """
    delivery_id = request.GET.get('delivery_id')
    
    if delivery_id:
        # Get specific delivery (for tracking by donors/receivers)
        delivery = DeliveryRequest.objects.filter(
            id=delivery_id
        ).select_related('donation').first()
    else:
        # Get active delivery for the current user (delivery agent)
        delivery = DeliveryRequest.objects.filter(
            delivery_agent=request.user,
            status__in=['accepted', 'picked_up']
        ).first()
    
    if delivery and delivery.current_latitude and delivery.current_longitude:
        receiver_address = ''
        if delivery.donation and delivery.donation.receiver and hasattr(delivery.donation.receiver, 'profile'):
            receiver_address = delivery.donation.receiver.profile.address
        
        return JsonResponse({
            'lat': float(delivery.current_latitude),
            'lng': float(delivery.current_longitude),
            'status': delivery.status,
            'speed': 0,
            'delivery_id': delivery.id,
            'donation_title': delivery.donation.title if delivery.donation else '',
            'pickup_address': delivery.donation.pickup_address if delivery.donation else '',
            'receiver_address': receiver_address,
        })
    else:
        # Return default location if no location tracked yet
        return JsonResponse({
            'lat': 19.0760,
            'lng': 72.8777,
            'status': 'collecting',
            'speed': 0,
            'delivery_id': delivery.id if delivery else None,
        })


@login_required
def update_location(request):
    """
    Update the current location of the delivery agent.
    Accepts POST with lat, lng, delivery_id.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = float(data.get('lat', 0))
            lng = float(data.get('lng', 0))
            delivery_id = data.get('delivery_id')
            
            if delivery_id:
                delivery = DeliveryRequest.objects.filter(
                    id=delivery_id,
                    delivery_agent=request.user
                ).first()
                
                if delivery:
                    delivery.current_latitude = lat
                    delivery.current_longitude = lng
                    delivery.last_location_update = timezone.now()
                    delivery.save()
                    return JsonResponse({'ok': True})
            
            return JsonResponse({'ok': False, 'error': 'Invalid delivery'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)


def tracker_view(request, delivery_id=None):
    """
    Render the live location tracker page.
    Accepts optional delivery_id to track specific delivery.
    """
    from django.conf import settings
    
    delivery = None
    donation = None
    
    if delivery_id:
        delivery = get_object_or_404(
            DeliveryRequest.objects.select_related('donation', 'donation__donor', 'donation__receiver', 'delivery_agent'),
            id=delivery_id
        )
        donation = delivery.donation
    
    # Get user's role to determine if they can update location
    user_role = None
    can_update = False
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        can_update = user_role == 'delivery' and delivery and delivery.delivery_agent == request.user
    
    return render(request, 'core/tracker.html', {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'delivery': delivery,
        'donation': donation,
        'can_update_location': can_update,
        'user_role': user_role,
    })

