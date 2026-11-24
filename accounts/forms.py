"""Registration, login and role-selection forms."""

import re

from django import forms
from django.contrib.auth.models import User

from .models import UserProfile


def _text(placeholder, **extra):
    attrs = {"class": "form-control", "placeholder": placeholder}
    attrs.update(extra)
    return forms.TextInput(attrs=attrs)


class RegistrationForm(forms.Form):
    """Collect everything needed to create a Django User plus its profile."""

    full_name = forms.CharField(max_length=150, widget=_text("Enter your full name"))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "name@example.com"}))
    mobile = forms.CharField(max_length=20, widget=_text("10-digit mobile number"))
    password1 = forms.CharField(
        label="Password (visible while typing)",
        strip=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your password", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm Password (visible while typing)",
        strip=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Repeat your password", "autocomplete": "new-password"}),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Role",
    )
    address = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Street, city, state and PIN code"}))
    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
        label="Profile Photo (optional)",
    )
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="I agree to the Terms & Conditions and privacy policy.",
    )

    def clean_full_name(self):
        value = self.cleaned_data["full_name"].strip()
        if len(value) < 3:
            raise forms.ValidationError("Please enter your full name (at least 3 characters).")
        return value

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please log in instead.")
        if UserProfile.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean_mobile(self):
        raw = self.cleaned_data["mobile"].strip().replace(" ", "").replace("-", "")
        number = re.sub(r"^(?:\+?91)", "", raw)
        if not re.fullmatch(r"[6-9]\d{9}", number):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number (e.g. 9876543210).")
        return number

    def clean_password2(self):
        # Only the two entries need to match. Simple passwords (including ones
        # similar to the name or email) are intentionally allowed on request.
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password and Confirm Password do not match.")
        return password2

    def save(self):
        """Create the hashed-password user and its profile. Call only after is_valid()."""
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            password=data["password1"],
            first_name=data["full_name"],
        )
        profile = user.profile
        profile.full_name = data["full_name"]
        profile.email = data["email"]
        profile.mobile = data["mobile"]
        profile.role = data["role"]
        profile.address = data["address"].strip()
        profile.gender = data["gender"]
        if data.get("profile_photo"):
            profile.profile_photo = data["profile_photo"]
        profile.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com", "autocomplete": "username"})
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter your password", "autocomplete": "current-password"}),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
        label="Select Your Role",
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Remember me on this device",
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
