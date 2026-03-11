from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, FoodDonation, FoodRequest, Feedback, DeliveryRequest


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    city = forms.CharField(max_length=100)
    pincode = forms.CharField(max_length=10)
    organization_name = forms.CharField(max_length=200, required=False,
                                         help_text="Required for donors (Restaurant, Hotel, etc.)")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                city=self.cleaned_data['city'],
                pincode=self.cleaned_data['pincode'],
                organization_name=self.cleaned_data.get('organization_name', ''),
            )
        return user


class FoodDonationForm(forms.ModelForm):
    class Meta:
        model = FoodDonation
        fields = ['title', 'description', 'food_type', 'quantity', 'serves_people',
                  'cooking_time', 'expiry_time', 'pickup_address', 'city', 'pincode', 'food_image']
        widgets = {
            'cooking_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiry_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'pickup_address': forms.Textarea(attrs={'rows': 2}),
        }


class FoodRequestForm(forms.ModelForm):
    class Meta:
        model = FoodRequest
        fields = ['people_count', 'food_preference', 'location', 'city', 'pincode', 'needed_by', 'notes']
        widgets = {
            'needed_by': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'location': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'city', 'pincode', 'organization_name', 'profile_pic', 'is_available']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

