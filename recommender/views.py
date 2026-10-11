import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .models import UserProfile, Prediction
from .ml.loader import predict_one, load_bundle

def is_staff(user):
    return user.is_authenticated and user.is_staff

def home(request):
    total_users = User.objects.filter(is_staff=False).count()
    total_predictions = Prediction.objects.count()
    context = {
        'total_users': total_users,
        'total_predictions': total_predictions
    }
    return render(request, "home.html", context)

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not name or not phone or not email or not password:
            messages.error(request, "Please fill in all fields.")
            return redirect("signup")
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect("signup")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("signup")

        with transaction.atomic():
            if " " in name:
                first_name, last_name = name.split(" ", 1)
            else:
                first_name = name
                last_name = ""
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.create(user=user, phone=phone)

        login(request, user)
        messages.success(request, "Account created successfully. Welcome!")
        return redirect("predict")

    return render(request, "signup.html")

@login_required
def predict_view(request):
    feature_order = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    result = None
    last_data = None
    if request.method == "POST":
        data = {}
        try:
            for c in feature_order:
                val = request.POST.get(c)
                if val is None:
                    raise ValueError(f"Missing {c}")
                data[c] = float(val)
        except (ValueError, TypeError):
            messages.error(request, "Invalid input. Please enter valid numeric values.")
            return redirect("predict")

        try:
            label = predict_one(data)
        except Exception as e:
            messages.error(request, "Unable to perform prediction: Model is unavailable or corrupt.")
            return redirect("predict")

        Prediction.objects.create(user=request.user, **data, predicted_label=label)
        result = label
        last_data = data
        messages.success(request, f"The recommended crop: {label}.")

    context = {
        'feature_order': feature_order,
        'result': result,
        'last_data': last_data
    }
    return render(request, "predict.html", context)

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid email or password.")
            return redirect("login")
        login(request, user)
        messages.success(request, "Logged in successfully.")
        return redirect("predict")
    return render(request, "login.html")

@login_required
def user_history_view(request):
    predictions = Prediction.objects.filter(user=request.user)
    return render(request, "history.html", {'predictions': predictions})

@login_required
@require_POST
def user_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id, user=request.user)
    prediction.delete()
    messages.success(request, "Deleted Successfully")
    return redirect("user_history")

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        if name:
            parts = name.split(" ", 1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts) > 1 else ""
        profile.phone = phone
        request.user.save()
        profile.save()
        messages.success(request, "Updated Successfully.")

    context = {
        'profile': profile,
        'full_name': request.user.get_full_name()
    }
    return render(request, "profile.html", context)

@login_required
def change_password_view(request):
    if request.method == "POST":
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_new_password")

        if not request.user.check_password(current):
            messages.error(request, "Current Password is Invalid.")
            return redirect("change_password")

        if len(new) < 6:
            messages.error(request, "New Password Must Be At Least 6 Characters.")
            return redirect("change_password")

        if new != confirm:
            messages.error(request, "New Passwords Do Not Match.")
            return redirect("change_password")

        request.user.set_password(new)
        request.user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        messages.success(request, "Password Changed successfully.")
        return redirect("change_password")

    return render(request, "change_password.html")

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid email or password.")
            return redirect("admin_login")

        if not user.is_staff:
            messages.error(request, "Access denied. Staff only.")
            return redirect("admin_login")

        login(request, user)
        messages.success(request, f"Welcome back, {user.username}.")
        return redirect("admin_dashboard")
    return render(request, "admin_login.html")

@user_passes_test(is_staff, login_url='admin_login')
def admin_dashboard_view(request):
    total_users = User.objects.filter(is_staff=False).count()
    total_predictions = Prediction.objects.count()

    crop_qs = (
        Prediction.objects.values("predicted_label")
        .annotate(c=Count("id"))
        .order_by("-c")[:10]
    )

    crop_labels = [i["predicted_label"].title() for i in crop_qs]
    crop_count = [i["c"] for i in crop_qs]

    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    # Optimize day counts query
    daily_predictions = (
        Prediction.objects.filter(created_at__date__gte=start_date)
        .values("created_at__date")
        .annotate(count=Count("id"))
    )

    predictions_by_date = {dp['created_at__date']: dp['count'] for dp in daily_predictions}

    days = [start_date + timedelta(days=i) for i in range(7)]
    day_labels = [d.strftime("%d %b") for d in days]
    day_counts = [predictions_by_date.get(d, 0) for d in days]

    context = {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "crop_labels": json.dumps(crop_labels),
        "crop_count": json.dumps(crop_count),
        "day_labels": json.dumps(day_labels),
        "day_counts": json.dumps(day_counts),
    }

    return render(request, "admin_dashboard.html", context)

@user_passes_test(is_staff, login_url='admin_login')
def admin_user_view(request):
    users = User.objects.filter(is_staff=False).select_related('userprofile')
    return render(request, "admin_view_users.html", {"users": users})

@user_passes_test(is_staff, login_url='admin_login')
@require_POST
def admin_user_delete(request, id):
    user = get_object_or_404(User, id=id)
    if user.is_staff or user.is_superuser:
        messages.error(request, "Cannot delete staff or superuser accounts.")
        return redirect("admin_view_users")

    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect("admin_view_users")

@user_passes_test(is_staff, login_url='admin_login')
def admin_predictions_view(request):
    qs = Prediction.objects.select_related('user')

    crop = request.GET.get('crop')
    start = request.GET.get('start')
    end = request.GET.get('end')

    d_start = parse_date(start) if start else None
    d_end = parse_date(end) if end else None

    if crop:
        qs = qs.filter(predicted_label__iexact=crop)
    if d_start:
        qs = qs.filter(created_at__date__gte=d_start)
    if d_end:
        qs = qs.filter(created_at__date__lte=d_end)

    crops = (
        Prediction.objects
        .order_by("predicted_label")
        .values_list("predicted_label", flat=True)
        .distinct()
    )

    context = {
        "qs": qs,
        "crops": crops,
        "current_crop": crop,
        "start": start,
        "end": end,
    }

    return render(request, "admin_predictions.html", context)

@user_passes_test(is_staff, login_url='admin_login')
@require_POST
def admin_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id)
    prediction.delete()
    messages.success(request, "Prediction deleted successfully.")
    return redirect("admin_predictions")

def admin_logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("admin_login")

def admin_change_password_view(request):
    if request.method == "POST":
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_new_password")

        if not request.user.check_password(current):
            messages.error(request, "Current Password is Invalid.")
            return redirect("admin_change")

        if len(new) < 6:
            messages.error(request, "New Password Must Be At Least 6 Characters.")
            return redirect("admin_change")

        if new != confirm:
            messages.error(request, "New Passwords Do Not Match.")
            return redirect("admin_change")

        request.user.set_password(new)
        request.user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        messages.success(request, "Password Changed successfully.")
        return redirect("admin_change")
    return render(request, "admin_change.html")
