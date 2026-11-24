"""Seven independent, permission-protected role dashboards."""

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import FIELD_ROLES, role_required
from accounts.models import UserProfile
from ConstructionManagement import models as cm


def dashboard_home(request):
    """Send every authenticated user to the dashboard for their role."""
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    profile = getattr(request.user, "profile", None)
    if profile is None:
        return redirect("accounts:login")
    return redirect(profile.get_dashboard_url())


def _live_stats():
    today = timezone.localdate()
    budget_allocated = cm.Budget.objects.aggregate(total=Sum("allocated"))["total"] or 0
    expenses_total = cm.Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    return {
        "projects": cm.Project.objects.count(),
        "sites": cm.Site.objects.count(),
        "active_sites": cm.Site.objects.filter(status=cm.StatusChoices.ACTIVE).count(),
        "activities": cm.Activity.objects.count(),
        "workers": cm.Labour.objects.count(),
        "materials": cm.Material.objects.count(),
        "low_stock": sum(1 for item in cm.Material.objects.all() if item.is_low),
        "contractors": cm.Contractor.objects.count(),
        "dprs": cm.DailyProgressReport.objects.count(),
        "open_issues": cm.SiteIssue.objects.filter(status__in=[cm.StatusChoices.ACTIVE, cm.StatusChoices.DELAYED]).count(),
        "budget_allocated": float(budget_allocated),
        "expenses_total": float(expenses_total),
        "present_today": cm.Attendance.objects.filter(date=today, status="PRESENT").count(),
        "quality_checks": cm.QualityInspection.objects.count(),
        "safety_checks": cm.SafetyInspection.objects.count(),
        "material_requests": cm.MaterialRequest.objects.count(),
        "material_movements": cm.MaterialTransaction.objects.count(),
        "avg_progress": round(
            float(cm.Site.objects.aggregate(avg=Avg("progress"))["avg"] or 0), 1
        ),
    }


def _base_context(request, page_title, page_icon):
    profile = request.user.profile
    return {
        "dashboard_shell": True,
        "page_title": page_title,
        "page_icon": page_icon,
        "role_label": profile.get_role_display(),
        "role_icon": profile.role_icon,
        "role_code": profile.role,
        "user_full_name": profile.full_name,
        "can_manage": profile.role == UserProfile.ROLE_BUILDER,
        "can_field": profile.role in FIELD_ROLES,
        "today": timezone.localdate(),
        "stats": _live_stats(),
        "notifications": cm.Notification.objects.all()[:5],
    }


@role_required(UserProfile.ROLE_BUILDER)
def builder_dashboard(request):
    context = _base_context(request, "Builder / Admin Dashboard", "bi-person-badge")
    context.update(
        {
            "projects": cm.Project.objects.all()[:8],
            "recent_activities": cm.Activity.objects.order_by("-start_date")[:6],
            "recent_expenses": cm.Expense.objects.all()[:6],
            "recent_dprs": cm.DailyProgressReport.objects.all()[:6],
            "low_stock_items": [m for m in cm.Material.objects.all() if m.is_low][:6],
        }
    )
    return render(request, "dashboards/builder.html", context)


@role_required(UserProfile.ROLE_SITE_ENGINEER)
def site_engineer_dashboard(request):
    context = _base_context(request, "Site Engineer Dashboard", "bi-ruler")
    context.update(
        {
            "sites": cm.Site.objects.all()[:8],
            "activities": cm.Activity.objects.order_by("-start_date")[:8],
            "quality": cm.QualityInspection.objects.all()[:6],
            "safety": cm.SafetyInspection.objects.all()[:6],
        }
    )
    return render(request, "dashboards/site_engineer.html", context)


@role_required(UserProfile.ROLE_SITE_SUPERVISOR)
def site_supervisor_dashboard(request):
    context = _base_context(request, "Site Supervisor Dashboard", "bi-hardhat")
    context.update(
        {
            "sites": cm.Site.objects.all()[:8],
            "activities": cm.Activity.objects.order_by("-start_date")[:8],
            "attendance": cm.Attendance.objects.all()[:8],
            "recent_dprs": cm.DailyProgressReport.objects.all()[:6],
            "open_issues": cm.SiteIssue.objects.filter(status=cm.StatusChoices.ACTIVE)[:6],
            "recent_photos": cm.ConstructionPhoto.objects.all()[:6],
        }
    )
    return render(request, "dashboards/site_supervisor.html", context)


@role_required(UserProfile.ROLE_CONTRACTOR)
def contractor_dashboard(request):
    context = _base_context(request, "Contractor Dashboard", "bi-briefcase")
    context.update(
        {
            "contractors": cm.Contractor.objects.all()[:12],
            "contract_value": float(
                cm.Contractor.objects.aggregate(total=Sum("contract_value"))["total"] or 0
            ),
            "activities": cm.Activity.objects.exclude(contractor__isnull=True).order_by("-start_date")[:8],
        }
    )
    return render(request, "dashboards/contractor.html", context)


@role_required(UserProfile.ROLE_STORE_MANAGER)
def store_manager_dashboard(request):
    context = _base_context(request, "Store Manager Dashboard", "bi-box-seam")
    context.update(
        {
            "materials": cm.Material.objects.all()[:12],
            "low_stock_items": [m for m in cm.Material.objects.all() if m.is_low][:10],
            "requests": cm.MaterialRequest.objects.all()[:8],
            "movements": cm.MaterialTransaction.objects.all()[:8],
        }
    )
    return render(request, "dashboards/store_manager.html", context)


@role_required(UserProfile.ROLE_ACCOUNTANT)
def accountant_dashboard(request):
    context = _base_context(request, "Accountant Dashboard", "bi-cash-coin")
    allocated = context["stats"]["budget_allocated"]
    spent = context["stats"]["expenses_total"]
    context.update(
        {
            "utilization": round((spent / allocated) * 100, 1) if allocated else 0,
            "budgets": cm.Budget.objects.all()[:10],
            "expenses": cm.Expense.objects.all()[:12],
            "projects": cm.Project.objects.all()[:8],
        }
    )
    return render(request, "dashboards/accountant.html", context)


@role_required(UserProfile.ROLE_LABOUR)
def labour_dashboard(request):
    context = _base_context(request, "Labour / Worker Dashboard", "bi-people")
    context.update(
        {
            "labour": cm.Labour.objects.all()[:12],
            "attendance": cm.Attendance.objects.all()[:12],
            "sites": cm.Site.objects.all()[:8],
        }
    )
    return render(request, "dashboards/labour.html", context)
