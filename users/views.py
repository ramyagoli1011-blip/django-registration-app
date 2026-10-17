
import re

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

from .db import users


def home(request):
    return render(request, "users/home.html")


def register(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        country = request.POST.get("country", "+91").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # 1. Check all required fields
        if not all([name, email, phone, password, confirm_password]):
            messages.error(request, "Please fill in all fields.")
            return render(request, "users/register.html")

        # 2. Validate email address
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            messages.error(request, "Enter a valid email address.")
            return render(request, "users/register.html")

        # 3. Validate phone number
        if not re.fullmatch(r"\d{10}", phone):
            messages.error(
                request,
                "Phone number must contain exactly 10 digits."
            )
            return render(request, "users/register.html")

        # 4. Validate country calling code
        if not re.fullmatch(r"\+\d{1,3}", country):
            messages.error(request, "Select a valid country code.")
            return render(request, "users/register.html")

        # 5. Validate password strength
        strong_password = (
            len(password) >= 8
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"\d", password)
            and re.search(r"[^A-Za-z0-9]", password)
        )

        if not strong_password:
            messages.error(
                request,
                "Password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, "
                "one number and one special character."
            )
            return render(request, "users/register.html")

        # 6. Confirm password
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "users/register.html")

        try:
            # 7. Check whether the email is already registered
            existing_user = users.find_one({"email": email})

            if existing_user:
                messages.error(
                    request,
                    "This email is already registered. Please log in."
                )
                return render(request, "users/register.html")

            # 8. Save the new user in MongoDB
            user_data = {
                "name": name,
                "email": email,
                "phone": country + phone,
                "password": make_password(password),
            }

            users.insert_one(user_data)

            # 9. Save registration status in session
            request.session["registered_email"] = email

            return redirect("success")

        except Exception:
            messages.error(
                request,
                "Registration failed. Please check your MongoDB "
                "connection and try again."
            )
            return render(request, "users/register.html")

    return render(request, "users/register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        # 1. Check required fields
        if not email or not password:
            messages.error(request, "Enter your email and password.")
            return render(request, "users/login.html")

        try:
            # 2. Find the user in MongoDB
            user = users.find_one({"email": email})

            # 3. Verify the password
            if not user or not check_password(
                password, user.get("password", "")
            ):
                messages.error(request, "Invalid email or password.")
                return render(request, "users/login.html")

            # 4. Start login session
            request.session["user_email"] = email

            # Clear previous registration-only session value
            request.session.pop("registered_email", None)

            return redirect("welcome")

        except Exception:
            messages.error(
                request,
                "Login failed. Please check your MongoDB connection "
                "and try again."
            )
            return render(request, "users/login.html")

    return render(request, "users/login.html")


def success(request):
    # Only show this page after a successful registration
    if not request.session.get("registered_email"):
        return redirect("register")

    return render(request, "users/success.html")


def welcome(request):
    # Check whether the user is logged in
    email = request.session.get("user_email")

    if not email:
        return redirect("login")

    try:
        # Find the logged-in user
        user = users.find_one({"email": email})

        if not user:
            request.session.flush()
            messages.error(request, "Please log in again.")
            return redirect("login")

        return render(
            request,
            "users/welcome.html",
            {"user": user}
        )

    except Exception:
        messages.error(
            request,
            "Unable to load your account. Please try again."
        )
        return redirect("login")


def logout_view(request):
    # Clear the session and log out
    request.session.flush()

    return redirect("home")
