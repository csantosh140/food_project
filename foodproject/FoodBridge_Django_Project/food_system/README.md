# 🌿 FoodBridge – Food Conservation & Distribution System

A Django-based platform that connects **Food Donors**, **Delivery Agents**, and **Receivers** to reduce food waste and feed those in need.

---

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Admin User (optional)
```bash
python manage.py createsuperuser
```

### 4. Start the Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 👥 Three User Roles

### 🏪 Food Donor (Restaurants, Hotels, Households)
- Register as a **Donor**
- Post surplus food donations with quantity, type, expiry time
- Track donation status (Available → Assigned → In Transit → Delivered)
- Receive notifications when food is picked up/delivered
- View history of all donations

### 🚚 Delivery Agent
- Register as a **Delivery Agent**
- Browse available food donations on the platform
- Accept delivery tasks and pick up food
- Update status: Picked Up → Delivered
- View full delivery history

### 🤲 Receiver (Individuals, NGOs, Shelters)
- Register as a **Receiver**
- Browse available food by city and type
- Request specific food donations
- Submit food requests for planned needs
- Give feedback after receiving food

---

## 🗂️ Project Structure

```
food_system/
├── food_system/         # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                # Main app
│   ├── models.py        # UserProfile, FoodDonation, DeliveryRequest, etc.
│   ├── views.py         # All views
│   ├── urls.py          # URL patterns
│   ├── forms.py         # Django forms
│   ├── admin.py         # Admin panel config
│   └── templates/core/  # HTML templates
│       ├── base.html
│       ├── home.html
│       ├── login.html
│       ├── register.html
│       ├── donor_dashboard.html
│       ├── delivery_dashboard.html
│       ├── receiver_dashboard.html
│       └── ... (more templates)
├── manage.py
└── requirements.txt
```

---

## 📊 Database Models

| Model | Description |
|-------|-------------|
| `UserProfile` | Extends User with role, phone, city, organization |
| `FoodDonation` | Food listing with type, quantity, expiry, status |
| `DeliveryRequest` | Links donation to delivery agent with status tracking |
| `FoodRequest` | Receiver's food request submissions |
| `Feedback` | Star ratings from receivers |
| `Notification` | In-app notifications for all users |

---

## 🔗 Key URLs

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/register/` | User registration |
| `/login/` | Login |
| `/dashboard/` | Role-based redirect |
| `/donor/` | Donor dashboard |
| `/donor/donate/` | Add new donation |
| `/delivery/` | Delivery dashboard |
| `/delivery/available/` | Browse available food |
| `/receiver/` | Receiver dashboard |
| `/receiver/browse/` | Browse food |
| `/admin/` | Django admin panel |

---

## 🌿 Impact

Every meal donated through FoodBridge:
- Reduces food waste from hotels, restaurants, and households
- Feeds people who genuinely need it
- Creates a community of compassionate donors and volunteers
