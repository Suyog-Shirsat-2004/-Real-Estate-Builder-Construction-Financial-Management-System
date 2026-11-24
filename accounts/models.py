"""User profile: role and extended account data for Django's built-in User."""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class UserProfile(models.Model):
    """One-to-one extension of ``auth.User`` with the system's role information."""

    ROLE_BUILDER = "BUILDER"
    ROLE_SITE_ENGINEER = "SITE_ENGINEER"
    ROLE_SITE_SUPERVISOR = "SITE_SUPERVISOR"
    ROLE_CONTRACTOR = "CONTRACTOR"
    ROLE_STORE_MANAGER = "STORE_MANAGER"
    ROLE_ACCOUNTANT = "ACCOUNTANT"
    ROLE_LABOUR = "LABOUR"

    ROLE_CHOICES = (
        (ROLE_BUILDER, "Builder / Admin"),
        (ROLE_SITE_ENGINEER, "Site Engineer"),
        (ROLE_SITE_SUPERVISOR, "Site Supervisor"),
        (ROLE_CONTRACTOR, "Contractor"),
        (ROLE_STORE_MANAGER, "Store Manager"),
        (ROLE_ACCOUNTANT, "Accountant"),
        (ROLE_LABOUR, "Labour / Worker"),
    )

    ROLE_ICONS = {
        ROLE_BUILDER: "bi-person-badge",
        ROLE_SITE_ENGINEER: "bi-ruler",
        ROLE_SITE_SUPERVISOR: "bi-hardhat",
        ROLE_CONTRACTOR: "bi-briefcase",
        ROLE_STORE_MANAGER: "bi-box-seam",
        ROLE_ACCOUNTANT: "bi-cash-coin",
        ROLE_LABOUR: "bi-people",
    }

    # Where each role lands immediately after a successful login.
    ROLE_DASHBOARDS = {
        ROLE_BUILDER: "dashboards:dashboard_builder",
        ROLE_SITE_ENGINEER: "dashboards:dashboard_site_engineer",
        ROLE_SITE_SUPERVISOR: "dashboards:dashboard_site_supervisor",
        ROLE_CONTRACTOR: "dashboards:dashboard_contractor",
        ROLE_STORE_MANAGER: "dashboards:dashboard_store_manager",
        ROLE_ACCOUNTANT: "dashboards:dashboard_accountant",
        ROLE_LABOUR: "dashboards:dashboard_labour",
    }

    GENDER_CHOICES = (
        ("", "Prefer not to say"),
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    )

    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"
    STATUS_SUSPENDED = "SUSPENDED"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_SUSPENDED, "Suspended"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True)
    mobile = models.CharField(max_length=20)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_BUILDER, db_index=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, null=True)
    account_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_registered"]

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def role_icon(self):
        return self.ROLE_ICONS.get(self.role, "bi-person")

    @property
    def is_active_account(self):
        return self.account_status == self.STATUS_ACTIVE and self.user.is_active

    def get_dashboard_url(self):
        """Return the dashboard for this profile's role."""
        return reverse(self.ROLE_DASHBOARDS.get(self.role, "home"))
