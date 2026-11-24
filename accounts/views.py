"""Registration, login, logout and password-reset support views."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.templatetags.static import static

from .forms import LoginForm, RegistrationForm
from .models import UserProfile

FIRST_VISIT_SESSION_KEY = "auth_login_page_visited"

# One simple logo per role, used on the login cards and in the side list.
ROLE_LOGOS = {
    UserProfile.ROLE_BUILDER: "images/builder-admin-logo.svg",
    UserProfile.ROLE_SITE_ENGINEER: "images/site-engineer-logo.svg",
    UserProfile.ROLE_SITE_SUPERVISOR: "images/site-supervisor-logo.svg",
    UserProfile.ROLE_CONTRACTOR: "images/contractor-logo.svg",
    UserProfile.ROLE_STORE_MANAGER: "images/store-manager-logo.svg",
    UserProfile.ROLE_ACCOUNTANT: "images/accountant-logo.svg",
    UserProfile.ROLE_LABOUR: "images/labour-worker-logo.svg",
}


def role_cards():
    """Build uniform role-card data with a logo for every role."""
    return [
        {
            "value": code,
            "label": label,
            "logo": static(ROLE_LOGOS[code]),
        }
        for code, label in UserProfile.ROLE_CHOICES
    ]


def register(request):
    if request.user.is_authenticated:
        return redirect(request.user.profile.get_dashboard_url())

    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES or None)
        if form.is_valid():
            try:
                # The unique username/email can still collide if the form is
                # submitted twice in quick succession (double-click / refresh).
                with transaction.atomic():
                    user = form.save()
            except IntegrityError:
                form.add_error(None, "This email address is already registered. Please log in instead.")
                messages.error(request, "Registration could not be completed. Please review the highlighted error.")
                return render(request, "accounts/register.html", {"form": form})
            request.session[FIRST_VISIT_SESSION_KEY] = True
            messages.success(
                request,
                f"Registration successful, {user.first_name}! Your account has been created. Please log in to continue.",
            )
            return redirect("accounts:login")
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect(request.user.profile.get_dashboard_url())

    # First-time visitor hint: shown once per session, not on every visit.
    show_first_visit_notice = not request.session.get(FIRST_VISIT_SESSION_KEY, False)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            selected_role = form.cleaned_data["role"]
            user = authenticate(request, username=email, password=password)

            if user is None:
                messages.error(request, "Invalid email address or password. Please try again.")
            else:
                profile = getattr(user, "profile", None)
                if profile is None or profile.role != selected_role:
                    messages.error(request, "The selected role does not match this account. Choose the role you registered with.")
                elif not profile.is_active_account:
                    messages.error(request, "This account is not active. Please contact the administrator.")
                else:
                    login(request, user)
                    if form.cleaned_data["remember_me"]:
                        request.session.set_expiry(60 * 60 * 24 * 14)
                    else:
                        request.session.set_expiry(0)
                    request.session[FIRST_VISIT_SESSION_KEY] = True
                    messages.success(request, f"Welcome back, {profile.full_name}!")
                    return redirect(profile.get_dashboard_url())
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()
        # The notice is consumed on the first GET of the login page.
        request.session[FIRST_VISIT_SESSION_KEY] = True

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "show_first_visit_notice": show_first_visit_notice,
            "roles": role_cards(),
        },
    )


def user_logout(request):
    # Only a real form submission may end a session (the navbar uses POST + CSRF).
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect("home")
