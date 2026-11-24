"""Reusable role-based access decorators."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import UserProfile

MANAGER_ROLES = (UserProfile.ROLE_BUILDER,)
FIELD_ROLES = (
    UserProfile.ROLE_BUILDER,
    UserProfile.ROLE_SITE_ENGINEER,
    UserProfile.ROLE_SITE_SUPERVISOR,
)


def role_required(*allowed_roles):
    """Allow only the listed roles (plus active accounts) to run a view."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if profile is None or not profile.is_active_account or profile.role not in allowed_roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("accounts:login")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def module_access_required(view_func):
    """Protect shared module views using their ``module`` argument.

    ``manager`` is reserved for the Builder/Admin workspace; ``supervisor`` is
    available to Builder, Site Engineer and Site Supervisor.
    """

    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        module = kwargs.get("module")
        if module is None and args:
            module = args[0]
        profile = getattr(request.user, "profile", None)
        allowed = MANAGER_ROLES if module == "manager" else FIELD_ROLES if module == "supervisor" else ()
        if profile is None or not profile.is_active_account or profile.role not in allowed:
            messages.error(request, "You do not have permission to access that page.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)

    return wrapped
