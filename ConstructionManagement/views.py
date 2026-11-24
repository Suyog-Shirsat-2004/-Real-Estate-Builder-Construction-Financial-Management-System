"""Views for the home page and the Site Manager / Site Supervisor modules."""

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import reduce
from operator import or_

from django.contrib import messages
from django.db.models import Avg, F, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from . import models
from .forms import FORMS, SearchForm


# ---------------------------------------------------------------------------
# Resource registry: one place that describes every CRUD page in the system.
# ---------------------------------------------------------------------------
RESOURCES = {
    "project": {
        "model": models.Project, "title": "Projects", "singular": "Project",
        "search": ["name", "code", "location", "client", "manager"],
        "fields": ["code", "name", "client", "location", "status", "progress"],
        "redirect": "manager_projects", "manager": "site_manager/projects.html",
        "supervisor": "site_manager/projects.html",
    },
    "site": {
        "model": models.Site, "title": "Construction Sites", "singular": "Site",
        "search": ["name", "code", "location", "supervisor"],
        "fields": ["code", "name", "project", "location", "status", "progress"],
        "redirect": "manager_sites", "manager": "site_manager/sites.html",
        "supervisor": "site_supervisor/assigned_sites.html",
    },
    "activity": {
        "model": models.Activity, "title": "Construction Activities", "singular": "Activity",
        "search": ["title", "activity_type", "assigned_to", "status"],
        "fields": ["title", "site", "activity_type", "start_date", "end_date", "status", "progress"],
        "redirect": "manager_activities", "manager": "site_manager/activities.html",
        "supervisor": "site_supervisor/work_updates.html",
    },
    "contractor": {
        "model": models.Contractor, "title": "Contractors", "singular": "Contractor",
        "search": ["name", "company", "contact_person", "email", "specialty"],
        "fields": ["name", "company", "specialty", "contract_value", "status"],
        "redirect": "manager_contractors", "manager": "site_manager/contractors.html",
    },
    "material": {
        "model": models.Material, "title": "Material Stock", "singular": "Material",
        "search": ["name", "category", "supplier"],
        "fields": ["name", "category", "unit", "quantity_in_stock", "reorder_level", "unit_cost"],
        "redirect": "manager_materials", "manager": "site_manager/materials.html",
        "supervisor": "site_supervisor/materials.html",
    },
    "material_request": {
        "model": models.MaterialRequest, "title": "Material Requests", "singular": "Material Request",
        "search": ["material__name", "requested_by", "site__name"],
        "fields": ["site", "material", "quantity", "request_date", "status"],
        "redirect": "manager_materials", "manager": "site_manager/materials.html",
    },
    "material_transaction": {
        "model": models.MaterialTransaction, "title": "Material Movements", "singular": "Material Movement",
        "search": ["material__name", "reference", "recorded_by", "site__name"],
        "fields": ["date", "site", "material", "transaction_type", "quantity", "recorded_by"],
        "redirect": "supervisor_receiving", "manager": "site_manager/materials.html",
        "supervisor": "site_supervisor/receiving.html",
    },
    "labour": {
        "model": models.Labour, "title": "Labour", "singular": "Worker",
        "search": ["name", "worker_id", "role", "phone"],
        "fields": ["worker_id", "name", "role", "site", "daily_wage", "status"],
        "redirect": "manager_labour", "manager": "site_manager/labour.html",
        "supervisor": "site_supervisor/attendance.html",
    },
    "attendance": {
        "model": models.Attendance, "title": "Labour Attendance", "singular": "Attendance",
        "search": ["labour__name", "labour__worker_id", "status"],
        "fields": ["date", "labour", "site", "status", "check_in", "check_out"],
        "redirect": "supervisor_attendance", "supervisor": "site_supervisor/attendance.html",
        "manager": "site_manager/labour.html",
    },
    "budget": {
        "model": models.Budget, "title": "Budget Overview", "singular": "Budget",
        "search": ["project__name", "category"],
        "fields": ["project", "category", "allocated", "spent", "year", "month"],
        "redirect": "manager_finance", "manager": "site_manager/finance.html",
    },
    "expense": {
        "model": models.Expense, "title": "Expense Details", "singular": "Expense",
        "search": ["category", "description", "vendor", "project__name"],
        "fields": ["date", "project", "category", "description", "amount", "status"],
        "redirect": "manager_finance", "manager": "site_manager/finance.html",
    },
    "dpr": {
        "model": models.DailyProgressReport, "title": "Daily Progress Reports", "singular": "Daily Progress Report",
        "search": ["site__name", "summary", "submitted_by", "status"],
        "fields": ["date", "site", "submitted_by", "progress_percentage", "status", "verified_by"],
        "redirect": "manager_dpr", "manager": "site_manager/dpr.html",
        "supervisor": "site_supervisor/dpr.html",
    },
    "milestone": {
        "model": models.ProjectMilestone, "title": "Project Timeline", "singular": "Milestone",
        "search": ["title", "project__name", "status"],
        "fields": ["title", "project", "due_date", "progress", "status"],
        "redirect": "manager_timeline", "manager": "site_manager/timeline.html",
    },
    "quality": {
        "model": models.QualityInspection, "title": "Quality Inspection", "singular": "Quality Inspection",
        "search": ["area", "inspector", "site__name"],
        "fields": ["inspection_date", "site", "area", "score", "status", "inspector"],
        "redirect": "manager_quality_safety", "manager": "site_manager/quality_safety.html",
        "supervisor": "site_supervisor/quality_checklist.html",
    },
    "safety": {
        "model": models.SafetyInspection, "title": "Safety Inspection", "singular": "Safety Inspection",
        "search": ["area", "inspector", "site__name"],
        "fields": ["inspection_date", "site", "area", "score", "status", "inspector"],
        "redirect": "manager_quality_safety", "manager": "site_manager/quality_safety.html",
        "supervisor": "site_supervisor/safety_checklist.html",
    },
    "issue": {
        "model": models.SiteIssue, "title": "Site Issues", "singular": "Site Issue",
        "search": ["title", "description", "reported_by"],
        "fields": ["title", "site", "severity", "status", "reported_date"],
        "redirect": "supervisor_issues", "supervisor": "site_supervisor/issues.html",
        "manager": "site_manager/reports.html",
    },
    "photo": {
        "model": models.ConstructionPhoto, "title": "Construction Photos", "singular": "Photo",
        "search": ["title", "caption", "site__name", "uploaded_by"],
        "fields": ["title", "site", "taken_at", "uploaded_by"],
        "redirect": "supervisor_photos", "supervisor": "site_supervisor/photos.html",
    },
    "notification": {
        "model": models.Notification, "title": "Notifications", "singular": "Notification",
        "search": ["title", "message", "category"],
        "fields": ["title", "category", "audience", "is_read", "created_at"],
        "redirect": "manager_notifications", "manager": "site_manager/notifications.html",
        "supervisor": "site_supervisor/notifications.html",
    },
}

MANAGER_PAGES = {
    "projects": "project", "sites": "site", "activities": "activity",
    "contractors": "contractor", "materials": "material", "labour": "labour",
    "dpr": "dpr", "timeline": "milestone",
}

SUPERVISOR_PAGES = {
    "assigned-sites": "site", "work-updates": "activity", "attendance": "attendance",
    "materials": "material", "receiving": "material_transaction", "photos": "photo",
    "dpr": "dpr", "issues": "issue", "quality-checklist": "quality",
    "safety-checklist": "safety", "notifications": "notification",
}


def _values(obj, field_names):
    rows = []
    for name in field_names:
        field = obj._meta.get_field(name)
        value = getattr(obj, name)
        if hasattr(value, "url") and name == "image":
            rows.append({"label": field.verbose_name.title(), "value": value.url, "is_image": True})
            continue
        rows.append({"label": field.verbose_name.title(), "value": value})
    return rows


def _chart_json(data):
    return json.dumps(data)


def _base_template(module):
    """Return the dedicated base template for the active module."""
    if module == "manager":
        return "ConstructionManagement/base_manager.html"
    return "ConstructionManagement/base_supervisor.html"


STATUS_BADGES = {
    "ACTIVE": "primary", "COMPLETED": "success", "PLANNED": "secondary",
    "DELAYED": "danger", "ON_HOLD": "warning", "CANCELLED": "dark",
    "HIGH": "warning", "CRITICAL": "danger", "MEDIUM": "info", "LOW": "success",
    "PRESENT": "success", "ABSENT": "danger", "HALF_DAY": "warning",
    "RECEIVED": "success", "CONSUMED": "warning",
}


def _fmt(value):
    """Convert model values into safe, readable JSON values."""
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Decimal):
        return f"{float(value):,.2f}"
    if isinstance(value, datetime):
        return value.strftime("%b %d, %Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%b %d, %Y")
    if isinstance(value, time):
        return value.strftime("%I:%M %p")
    return str(value)


def _badge(value):
    return STATUS_BADGES.get(str(getattr(value, "value", value)), "secondary")


def _row(label, value, note=None, link=None, badge=None, badge_label=None):
    row = {"label": str(label), "value": _fmt(value)}
    if note:
        row["note"] = str(note)
    if link:
        row["link"] = link
    if badge:
        row["badge"] = badge
        row["badge_label"] = _fmt(badge_label if badge_label is not None else value)
    return row


def _detail_payload(module, section):
    """Build the deep-detail payload for a clickable dashboard card."""
    today = timezone.localdate()
    prefix = "manager" if module == "manager" else "supervisor"

    def link(resource, pk):
        return reverse(f"{prefix}_detail", args=[resource, pk])

    payload = {
        "title": "Dashboard details",
        "subtitle": "Live records from the construction database.",
        "icon": "bi-list-ul",
        "sections": [],
    }

    def add(heading, rows):
        payload["sections"].append({"heading": heading, "rows": rows})

    def project_rows(qs):
        return [
            _row(
                f"{p.code} - {p.name}",
                f"{p.get_status_display()} | {p.progress}%",
                note=f"Client: {_fmt(p.client)} | Location: {_fmt(p.location)} | Budget: {_fmt(p.budget)} | Manager: {_fmt(p.manager)}",
                link=link("project", p.pk),
                badge=_badge(p.status),
            )
            for p in qs
        ]

    def site_rows(qs):
        return [
            _row(
                f"{s.code} - {s.name}",
                f"{s.get_status_display()} | {s.progress}%",
                note=f"Project: {_fmt(s.project.name)} | Location: {_fmt(s.location)} | Supervisor: {_fmt(s.supervisor)} | Area: {_fmt(s.area_sqft)} sqft",
                link=link("site", s.pk),
                badge=_badge(s.status),
            )
            for s in qs
        ]

    def activity_rows(qs):
        return [
            _row(
                a.title,
                f"{a.get_status_display()} | {a.progress}%",
                note=f"Site: {_fmt(a.site.name)} | Type: {_fmt(a.activity_type)} | {_fmt(a.start_date)} to {_fmt(a.end_date)} | Assigned: {_fmt(a.assigned_to)}",
                link=link("activity", a.pk),
                badge=_badge(a.status),
            )
            for a in qs
        ]

    def dpr_rows(qs):
        return [
            _row(
                f"{d.site.name} - {_fmt(d.date)}",
                d.get_status_display(),
                note=f"Progress: {d.progress_percentage}% | Labour: {d.labour_count} | Submitted by: {_fmt(d.submitted_by)} | Verified by: {_fmt(d.verified_by)} | Issues: {_fmt(d.issues)}",
                link=link("dpr", d.pk),
                badge=_badge(d.status),
            )
            for d in qs
        ]

    def material_rows(qs):
        return [
            _row(
                m.name,
                f"{_fmt(m.quantity_in_stock)} {_fmt(m.unit)}",
                note=f"Category: {_fmt(m.category)} | Reorder level: {_fmt(m.reorder_level)} | Unit cost: {_fmt(m.unit_cost)} | Supplier: {_fmt(m.supplier)}",
                link=link("material", m.pk),
                badge="danger" if m.is_low else "success",
                badge_label="Low stock" if m.is_low else "In stock",
            )
            for m in qs
        ]

    projects = models.Project.objects.all()
    sites = models.Site.objects.all()
    activities = models.Activity.objects.all()

    if section == "kpi_projects":
        payload.update(title="All Projects", icon="bi-diagram-3", subtitle="Every project, its financials, timeline and delivery status.")
        add("Summary", [
            _row("Total projects", projects.count()),
            _row("Active projects", projects.filter(status=models.StatusChoices.ACTIVE).count()),
            _row("Completed projects", projects.filter(status=models.StatusChoices.COMPLETED).count()),
            _row("Total budget", projects.aggregate(total=Sum("budget"))["total"] or 0),
        ])
        add("Projects", project_rows(projects))

    elif section in ("kpi_sites", "kpi_active_sites", "kpi_completed_sites", "assigned_sites"):
        qs = sites
        if section == "kpi_active_sites":
            qs = qs.filter(status=models.StatusChoices.ACTIVE)
        elif section == "kpi_completed_sites":
            qs = qs.filter(status=models.StatusChoices.COMPLETED)
        payload.update(title="Construction Sites", icon="bi-geo-alt", subtitle="Site location, supervisor, progress and completion data.")
        add("Summary", [
            _row("Total sites", sites.count()),
            _row("Active sites", sites.filter(status=models.StatusChoices.ACTIVE).count()),
            _row("Completed sites", sites.filter(status=models.StatusChoices.COMPLETED).count()),
        ])
        add("Sites", site_rows(qs))

    elif section in ("kpi_pending_activities", "kpi_delayed_activities", "kpi_today_activities", "kpi_completed_activities", "kpi_ongoing_activities", "recent_activities", "activities", "pending_tasks"):
        qs = activities
        if section == "kpi_pending_activities":
            qs = qs.filter(status=models.StatusChoices.PLANNED)
        elif section == "kpi_delayed_activities":
            qs = qs.filter(status=models.StatusChoices.DELAYED)
        elif section == "kpi_completed_activities":
            qs = qs.filter(status=models.StatusChoices.COMPLETED)
        elif section == "kpi_ongoing_activities":
            qs = qs.filter(status=models.StatusChoices.ACTIVE)
        elif section == "kpi_today_activities":
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
        elif section in ("recent_activities", "activities"):
            qs = qs.order_by("-start_date")[:15]
        elif section == "pending_tasks":
            qs = qs.filter(status=models.StatusChoices.PLANNED)
        payload.update(title="Construction Activities", icon="bi-list-check", subtitle="Work items with site, contractor, schedule and assignment details.")
        add("Summary", [
            _row("Total activities", activities.count()),
            _row("Planned", activities.filter(status=models.StatusChoices.PLANNED).count()),
            _row("Active", activities.filter(status=models.StatusChoices.ACTIVE).count()),
            _row("Completed", activities.filter(status=models.StatusChoices.COMPLETED).count()),
            _row("Delayed", activities.filter(status=models.StatusChoices.DELAYED).count()),
        ])
        add("Activities", activity_rows(qs))

    elif section == "kpi_contractors":
        payload.update(title="Contractors", icon="bi-people", subtitle="Contract values, specialties, contacts and performance ratings.")
        add("Summary", [
            _row("Total contractors", models.Contractor.objects.count()),
            _row("Active contractors", models.Contractor.objects.filter(status=models.StatusChoices.ACTIVE).count()),
            _row("Total contract value", models.Contractor.objects.aggregate(total=Sum("contract_value"))["total"] or 0),
        ])
        add("Contractors", [
            _row(
                f"{c.name} ({c.company})",
                _fmt(c.contract_value),
                note=f"Specialty: {_fmt(c.specialty)} | Contact: {_fmt(c.contact_person)} {_fmt(c.phone)} | Rating: {c.rating}/5 | {_fmt(c.start_date)} to {_fmt(c.end_date)}",
                link=link("contractor", c.pk),
                badge=_badge(c.status),
            )
            for c in models.Contractor.objects.all()
        ])

    elif section == "kpi_labour":
        payload.update(title="Labour Directory", icon="bi-person-badge", subtitle="Every worker with role, wage, site and joining details.")
        add("Summary", [
            _row("Total workers", models.Labour.objects.count()),
            _row("Active workers", models.Labour.objects.filter(status=models.StatusChoices.ACTIVE).count()),
            _row("Daily wage bill", models.Labour.objects.filter(status=models.StatusChoices.ACTIVE).aggregate(total=Sum("daily_wage"))["total"] or 0),
        ])
        add("Workers", [
            _row(
                f"{w.worker_id} - {w.name}",
                _fmt(w.daily_wage),
                note=f"Role: {_fmt(w.role)} | Site: {_fmt(w.site.name if w.site else '-')} | Phone: {_fmt(w.phone)} | Joined: {_fmt(w.join_date)}",
                link=link("labour", w.pk),
                badge=_badge(w.status),
            )
            for w in models.Labour.objects.all()
        ])

    elif section in ("kpi_materials", "low_materials"):
        qs = models.Material.objects.all()
        if section == "low_materials":
            qs = qs.filter(quantity_in_stock__lte=F("reorder_level"))
        payload.update(title="Material Stock", icon="bi-box-seam", subtitle="Current stock, reorder levels, unit costs and suppliers.")
        add("Summary", [
            _row("Material types", models.Material.objects.count()),
            _row("Low stock items", models.Material.objects.filter(quantity_in_stock__lte=F("reorder_level")).count()),
            _row("Stock value", sum(float(m.quantity_in_stock) * float(m.unit_cost) for m in models.Material.objects.all())),
        ])
        add("Materials", material_rows(qs))

    elif section in ("kpi_budget", "monthly_expense"):
        budgets = models.Budget.objects.all()
        expenses = models.Expense.objects.all()
        allocated = float(budgets.aggregate(total=Sum("allocated"))["total"] or 0)
        spent = float(budgets.aggregate(total=Sum("spent"))["total"] or 0)
        payload.update(title="Budget & Expenses", icon="bi-cash-coin", subtitle="Allocations, spending, utilization and monthly expense trend.")
        add("Summary", [
            _row("Total allocated", allocated),
            _row("Total spent", spent),
            _row("Utilization", f"{round((spent / allocated) * 100, 1) if allocated else 0}%"),
            _row("Total expenses", expenses.aggregate(total=Sum("amount"))["total"] or 0),
        ])
        monthly_rows = []
        for offset in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=30 * offset)
            total = expenses.filter(date__year=month_date.year, date__month=month_date.month).aggregate(total=Sum("amount"))["total"] or 0
            monthly_rows.append(_row(month_date.strftime("%B %Y"), total))
        add("Monthly expense trend", monthly_rows)
        add("Budgets", [
            _row(
                f"{b.project.name} - {b.category}",
                f"{_fmt(b.allocated)} allocated / {_fmt(b.spent)} spent",
                note=f"Utilization: {b.utilization}% | Period: {b.month}/{b.year} | {_fmt(b.notes)}",
                link=link("budget", b.pk),
            )
            for b in budgets
        ])
        add("Recent expenses", [
            _row(
                f"{e.category} - {_fmt(e.description)}",
                e.amount,
                note=f"Project: {_fmt(e.project.name)} | Vendor: {_fmt(e.vendor)} | Approved by: {_fmt(e.approved_by)}",
                link=link("expense", e.pk),
                badge=_badge(e.status),
            )
            for e in expenses.order_by("-date")[:12]
        ])

    elif section in ("project_progress", "projects_table"):
        payload.update(title="Project Progress", icon="bi-bar-chart-line", subtitle="Detailed progress, finance and schedule for every project.")
        add("Projects", project_rows(projects))

    elif section == "activity_status":
        payload.update(title="Activity Status Breakdown", icon="bi-pie-chart", subtitle="Count of work items in each lifecycle stage.")
        add("Status counts", [
            _row(choice.label, activities.filter(status=choice.value).count(), badge=STATUS_BADGES.get(choice.value, "secondary"), badge_label=choice.label)
            for choice in models.StatusChoices
        ])

    elif section in ("pending_approvals", "kpi_pending_dpr"):
        qs = models.DailyProgressReport.objects.filter(status=models.StatusChoices.PLANNED)
        payload.update(title="Pending DPR Approvals", icon="bi-check2-square", subtitle="Daily progress reports waiting for manager verification.")
        add("Pending reports", dpr_rows(qs))

    elif section == "recent_notifications":
        payload.update(title="Notifications", icon="bi-bell", subtitle="All system notifications with audience and read status.")
        add("Notifications", [
            _row(
                n.title,
                "Read" if n.is_read else "Unread",
                note=f"Category: {_fmt(n.category)} | Audience: {n.get_audience_display()} | {_fmt(n.created_at)} | {_fmt(n.message)}",
                link=link("notification", n.pk),
                badge="success" if n.is_read else "warning",
            )
            for n in models.Notification.objects.all()[:20]
        ])

    elif section == "upcoming_deadlines":
        payload.update(title="Upcoming Deadlines", icon="bi-calendar-week", subtitle="Milestones due from today onward.")
        add("Milestones", [
            _row(
                m.title,
                _fmt(m.due_date),
                note=f"Project: {_fmt(m.project.name)} | Progress: {m.progress}% | {_fmt(m.description)}",
                link=link("milestone", m.pk),
                badge=_badge(m.status),
            )
            for m in models.ProjectMilestone.objects.filter(due_date__gte=today).order_by("due_date")
        ])

    elif section in ("kpi_present_workers", "kpi_absent_workers"):
        status = "PRESENT" if section == "kpi_present_workers" else "ABSENT"
        payload.update(title="Labour Attendance", icon="bi-person-check", subtitle=f"Workers marked {status.lower().replace('_', ' ')} today.")
        add("Attendance", [
            _row(
                f"{a.labour.name} ({a.labour.worker_id})",
                a.get_status_display(),
                note=f"Site: {_fmt(a.site.name if a.site else '-')} | Check-in: {_fmt(a.check_in)} | Check-out: {_fmt(a.check_out)} | {_fmt(a.remarks)}",
                link=link("attendance", a.pk),
                badge=_badge(a.status),
            )
            for a in models.Attendance.objects.filter(date=today, status=status)
        ])

    elif section in ("kpi_material_received", "kpi_material_consumed"):
        tx_type = "RECEIVED" if section == "kpi_material_received" else "CONSUMED"
        payload.update(title="Material Movement", icon="bi-box-arrow-in-down" if tx_type == "RECEIVED" else "bi-box-arrow-up", subtitle=f"Materials {tx_type.lower()} today.")
        add("Transactions", [
            _row(
                f"{t.material.name} at {t.site.name}",
                f"{_fmt(t.quantity)} {_fmt(t.material.unit)}",
                note=f"Reference: {_fmt(t.reference)} | Recorded by: {_fmt(t.recorded_by)} | {_fmt(t.notes)}",
                link=link("material_transaction", t.pk),
                badge=_badge(t.transaction_type),
            )
            for t in models.MaterialTransaction.objects.filter(date=today, transaction_type=tx_type)
        ])

    elif section == "kpi_open_issues":
        payload.update(title="Open Site Issues", icon="bi-exclamation-circle", subtitle="Active issues reported from the field.")
        add("Issues", [
            _row(
                i.title,
                i.get_severity_display(),
                note=f"Site: {_fmt(i.site.name)} | Reported by: {_fmt(i.reported_by)} | {_fmt(i.reported_date)} | Resolution: {_fmt(i.resolution)}",
                link=link("issue", i.pk),
                badge=_badge(i.severity),
            )
            for i in models.SiteIssue.objects.filter(status=models.StatusChoices.ACTIVE)
        ])

    elif section == "issue_alerts":
        payload.update(title="Issue Alerts", icon="bi-exclamation-triangle", subtitle="Open site issues requiring attention.")
        add("Issues", [
            _row(
                i.title,
                i.get_severity_display(),
                note=f"Site: {_fmt(i.site.name)} | Status: {i.get_status_display()} | {_fmt(i.description)}",
                link=link("issue", i.pk),
                badge=_badge(i.severity),
            )
            for i in models.SiteIssue.objects.filter(status=models.StatusChoices.ACTIVE)
        ])

    elif section == "kpi_safety_alerts":
        payload.update(title="Safety Alerts", icon="bi-shield-exclamation", subtitle="Safety inspections flagged as delayed.")
        add("Safety inspections", [
            _row(
                f"{s.site.name} - {_fmt(s.area)}",
                s.get_status_display(),
                note=f"Date: {_fmt(s.inspection_date)} | Score: {s.score} | Inspector: {_fmt(s.inspector)} | {_fmt(s.findings)}",
                link=link("safety", s.pk),
                badge=_badge(s.status),
            )
            for s in models.SafetyInspection.objects.filter(status=models.StatusChoices.DELAYED)
        ])

    elif section == "progress_chart":
        payload.update(title="Daily Progress Trend", icon="bi-graph-up", subtitle="Average DPR progress percentage over the last seven days.")
        rows = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            avg = models.DailyProgressReport.objects.filter(date=day).aggregate(avg=Avg("progress_percentage"))["avg"] or 0
            rows.append(_row(day.strftime("%A, %b %d"), f"{round(float(avg), 1)}%"))
        add("Progress by day", rows)

    elif section == "recent_photos":
        payload.update(title="Construction Photos", icon="bi-camera", subtitle="Latest site photographs uploaded from the field.")
        add("Photos", [
            _row(
                p.title,
                _fmt(p.taken_at),
                note=f"Site: {_fmt(p.site.name)} | Uploaded by: {_fmt(p.uploaded_by)} | {_fmt(p.caption)}",
                link=link("photo", p.pk),
            )
            for p in models.ConstructionPhoto.objects.all()[:20]
        ])

    else:
        payload.update(title="Dashboard Details", icon="bi-info-circle", subtitle="Detailed record information.")
        add("Information", [_row("Section", section)])

    return payload


def dashboard_detail(request, module, section):
    """Return JSON details for a clickable dashboard card."""
    return JsonResponse(_detail_payload(module, section))


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
def home(request):
    context = {
        "projects_count": models.Project.objects.count(),
        "sites_count": models.Site.objects.count(),
        "active_sites": models.Site.objects.filter(status=models.StatusChoices.ACTIVE).count(),
        "activities_count": models.Activity.objects.count(),
        "workers_count": models.Labour.objects.count(),
    }
    return render(request, "ConstructionManagement/home.html", context)


def about(request):
    return render(request, "ConstructionManagement/about.html")


# ---------------------------------------------------------------------------
# Generic CRUD
# ---------------------------------------------------------------------------
def resource_list(request, module, key, queryset=None, page_title=None):
    cfg = RESOURCES[key]
    qs = queryset if queryset is not None else cfg["model"].objects.all()
    search_form = SearchForm(request.GET or None)
    q = request.GET.get("q", "").strip()
    if q:
        query = reduce(or_, (Q(f"{field}__icontains", q) for field in cfg["search"]))
        qs = qs.filter(query)
    status = request.GET.get("status", "")
    if status and "status" in [f.name for f in cfg["model"]._meta.fields]:
        qs = qs.filter(status=status)

    template = cfg.get(module, "generic/list.html")
    if isinstance(template, str) and not template.startswith("ConstructionManagement/"):
        template = f"ConstructionManagement/{template}"

    context = {
        "module": module,
        "base_template": _base_template(module),
        "resource_key": key,
        "resource": cfg,
        "objects": qs,
        "title": page_title or cfg["title"],
        "search_form": search_form,
        "fields": cfg["fields"],
        "query": q,
        "status_filter": status,
        "has_status": "status" in [f.name for f in cfg["model"]._meta.fields],
        "density": request.session.get("table_density", "comfortable"),
    }
    return render(request, template, context)


def resource_detail(request, module, key, pk):
    cfg = RESOURCES[key]
    obj = get_object_or_404(cfg["model"], pk=pk)
    template = "ConstructionManagement/generic/photo_detail.html" if key == "photo" else "ConstructionManagement/generic/detail.html"
    return render(request, template, {
        "module": module, "base_template": _base_template(module),
        "resource_key": key, "resource": cfg, "object": obj,
        "rows": _values(obj, [f.name for f in cfg["model"]._meta.fields if f.name not in ("id",)]),
        "title": str(obj),
    })


def resource_form(request, module, key, pk=None):
    cfg = RESOURCES[key]
    Form = FORMS[key]
    obj = get_object_or_404(cfg["model"], pk=pk) if pk else None
    form_kwargs = {"module": module} if key == "photo" else {}
    if request.method == "POST":
        form = Form(request.POST, request.FILES or None, instance=obj, **form_kwargs)
        if form.is_valid():
            form.save()
            success_message = getattr(form, "success_message", None) or f"{cfg['singular']} saved successfully."
            messages.success(request, success_message)
            return redirect(cfg["redirect"])
        messages.error(request, "Please correct the errors below.")
    else:
        form = Form(instance=obj, **form_kwargs)
    return render(request, "ConstructionManagement/generic/form.html", {
        "module": module, "base_template": _base_template(module),
        "resource_key": key, "resource": cfg, "form": form, "object": obj,
        "title": f"{'Edit' if obj else 'Add'} {cfg['singular']}",
    })


def resource_delete(request, module, key, pk):
    cfg = RESOURCES[key]
    obj = get_object_or_404(cfg["model"], pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"{cfg['singular']} deleted successfully.")
        return redirect(cfg["redirect"])
    return render(request, "ConstructionManagement/generic/confirm_delete.html", {
        "module": module, "base_template": _base_template(module),
        "resource_key": key, "resource": cfg, "object": obj, "title": f"Delete {cfg['singular']}",
    })


def verify_dpr(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden()
    dpr = get_object_or_404(models.DailyProgressReport, pk=pk)
    dpr.status = models.StatusChoices.COMPLETED
    dpr.verified_by = "Site Manager"
    dpr.verified_date = timezone.localdate()
    dpr.save(update_fields=["status", "verified_by", "verified_date"])
    messages.success(request, "DPR verified successfully.")
    return redirect("manager_dpr")


def mark_notification_read(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden()
    notification = get_object_or_404(models.Notification, pk=pk)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    messages.success(request, "Notification marked as read.")
    module = request.POST.get("module", "manager")
    return redirect("manager_notifications" if module == "manager" else "supervisor_notifications")


# ---------------------------------------------------------------------------
# Site Manager dashboard and special pages
# ---------------------------------------------------------------------------
def manager_dashboard(request):
    today = timezone.localdate()
    month_ago = today - timedelta(days=30)
    projects = models.Project.objects.all()
    sites = models.Site.objects.all()
    activities = models.Activity.objects.all()
    budgets = models.Budget.objects.all()

    allocated = float(budgets.aggregate(total=Sum("allocated"))["total"] or 0)
    spent = float(budgets.aggregate(total=Sum("spent"))["total"] or 0)
    utilization = round((spent / allocated) * 100, 1) if allocated else 0

    monthly = []
    for offset in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=30 * offset))
        total = models.Expense.objects.filter(date__year=month_date.year, date__month=month_date.month).aggregate(total=Sum("amount"))["total"] or 0
        monthly.append({"label": month_date.strftime("%b"), "value": float(total)})

    status_counts = {choice.value: activities.filter(status=choice.value).count() for choice in models.StatusChoices}

    context = {
        "module": "manager",
        "base_template": _base_template("manager"),
        "title": "Site Manager Dashboard",
        "kpis": [
            {"section": "kpi_projects", "label": "Total Assigned Projects", "value": projects.count(), "icon": "bi-diagram-3", "color": "primary"},
            {"section": "kpi_sites", "label": "Total Construction Sites", "value": sites.count(), "icon": "bi-geo-alt", "color": "info"},
            {"section": "kpi_active_sites", "label": "Active Sites", "value": sites.filter(status=models.StatusChoices.ACTIVE).count(), "icon": "bi-building", "color": "success"},
            {"section": "kpi_completed_sites", "label": "Completed Sites", "value": sites.filter(status=models.StatusChoices.COMPLETED).count(), "icon": "bi-check-circle", "color": "secondary"},
            {"section": "kpi_pending_activities", "label": "Pending Activities", "value": activities.filter(status=models.StatusChoices.PLANNED).count(), "icon": "bi-hourglass-split", "color": "warning"},
            {"section": "kpi_delayed_activities", "label": "Delayed Activities", "value": activities.filter(status=models.StatusChoices.DELAYED).count(), "icon": "bi-exclamation-triangle", "color": "danger"},
            {"section": "kpi_contractors", "label": "Total Contractors", "value": models.Contractor.objects.count(), "icon": "bi-people", "color": "primary"},
            {"section": "kpi_labour", "label": "Total Labour", "value": models.Labour.objects.count(), "icon": "bi-person-badge", "color": "info"},
            {"section": "kpi_materials", "label": "Material Availability", "value": models.Material.objects.filter(quantity_in_stock__gt=0).count(), "icon": "bi-box-seam", "color": "success"},
            {"section": "kpi_budget", "label": "Budget Utilization", "value": f"{utilization}%", "icon": "bi-cash-coin", "color": "warning"},
        ],
        "projects": projects[:8],
        "recent_activities": activities.order_by("-start_date")[:6],
        "pending_approvals": models.DailyProgressReport.objects.filter(status=models.StatusChoices.PLANNED)[:5],
        "recent_notifications": models.Notification.objects.all()[:5],
        "upcoming_deadlines": models.ProjectMilestone.objects.filter(due_date__gte=today).order_by("due_date")[:5],
        "project_chart": _chart_json({
            "labels": [p.name[:18] for p in projects[:8]],
            "values": [p.progress for p in projects[:8]],
        }),
        "expense_chart": _chart_json({
            "labels": [m["label"] for m in monthly],
            "values": [m["value"] for m in monthly],
        }),
        "activity_chart": _chart_json({
            "labels": [choice.label for choice in models.StatusChoices],
            "values": [status_counts[choice.value] for choice in models.StatusChoices],
        }),
        "low_materials": models.Material.objects.filter(quantity_in_stock__lte=F("reorder_level"))[:5],
    }
    return render(request, "ConstructionManagement/site_manager/dashboard.html", context)


def manager_page(request, page):
    if page == "dashboard":
        return manager_dashboard(request)
    if page == "finance":
        return finance(request, "manager")
    if page == "reports":
        return reports(request, "manager")
    if page == "quality-safety":
        return quality_safety(request, "manager")
    if page == "settings":
        return settings_page(request, "manager")
    if page == "notifications":
        return resource_list(request, "manager", "notification", page_title="Notifications")
    if page in MANAGER_PAGES:
        return resource_list(request, "manager", MANAGER_PAGES[page])
    messages.error(request, "The requested page does not exist.")
    return redirect("manager_dashboard")


def finance(request, module):
    budgets = models.Budget.objects.all()
    expenses = models.Expense.objects.all()
    allocated = float(budgets.aggregate(total=Sum("allocated"))["total"] or 0)
    spent = float(budgets.aggregate(total=Sum("spent"))["total"] or 0)
    return render(request, "ConstructionManagement/site_manager/finance.html", {
        "module": module, "base_template": _base_template(module), "title": "Budget & Expenses",
        "budgets": budgets, "expenses": expenses,
        "allocated": allocated, "spent": spent,
        "utilization": round((spent / allocated) * 100, 1) if allocated else 0,
        "expense_chart": _chart_json({
            "labels": list(expenses.values_list("category", flat=True)[:8]),
            "values": [float(v) for v in expenses.values_list("amount", flat=True)[:8]],
        }),
    })


def reports(request, module):
    module_dir = "site_manager" if module == "manager" else "site_supervisor"
    return render(request, f"ConstructionManagement/{module_dir}/reports.html", {
        "module": module, "base_template": _base_template(module), "title": "Reports",
        "projects": models.Project.objects.all(),
        "dprs": models.DailyProgressReport.objects.all()[:10],
        "expenses": models.Expense.objects.all()[:10],
        "issues": models.SiteIssue.objects.all()[:10],
        "total_expense": models.Expense.objects.aggregate(total=Sum("amount"))["total"] or 0,
    })


def quality_safety(request, module):
    module_dir = "site_manager" if module == "manager" else "site_supervisor"
    return render(request, f"ConstructionManagement/{module_dir}/quality_safety.html", {
        "module": module, "base_template": _base_template(module), "title": "Quality & Safety",
        "quality": models.QualityInspection.objects.all()[:10],
        "safety": models.SafetyInspection.objects.all()[:10],
    })


def settings_page(request, module):
    module_dir = "site_manager" if module == "manager" else "site_supervisor"
    if request.method == "POST":
        density = request.POST.get("density", "comfortable")
        request.session["table_density"] = density
        messages.success(request, "Preferences saved for this session.")
    return render(request, f"ConstructionManagement/{module_dir}/settings.html", {
        "module": module, "base_template": _base_template(module), "title": "Settings",
        "density": request.session.get("table_density", "comfortable"),
    })


# ---------------------------------------------------------------------------
# Site Supervisor dashboard and special pages
# ---------------------------------------------------------------------------
def supervisor_dashboard(request):
    today = timezone.localdate()
    sites = models.Site.objects.all()
    activities = models.Activity.objects.all()
    attendance_today = models.Attendance.objects.filter(date=today)
    transactions = models.MaterialTransaction.objects.filter(date=today)

    progress_days = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        avg = models.DailyProgressReport.objects.filter(date=day).aggregate(avg=Avg("progress_percentage"))["avg"] or 0
        progress_days.append({"label": day.strftime("%a"), "value": round(float(avg), 1)})

    context = {
        "module": "supervisor",
        "base_template": _base_template("supervisor"),
        "title": "Site Supervisor Dashboard",
        "kpis": [
            {"section": "kpi_sites", "label": "Assigned Construction Sites", "value": sites.count(), "icon": "bi-geo-alt", "color": "primary"},
            {"section": "kpi_today_activities", "label": "Today's Activities", "value": activities.filter(start_date__lte=today, end_date__gte=today).count(), "icon": "bi-calendar-check", "color": "info"},
            {"section": "kpi_completed_activities", "label": "Completed Activities", "value": activities.filter(status=models.StatusChoices.COMPLETED).count(), "icon": "bi-check2-square", "color": "success"},
            {"section": "kpi_ongoing_activities", "label": "Ongoing Activities", "value": activities.filter(status=models.StatusChoices.ACTIVE).count(), "icon": "bi-play-circle", "color": "primary"},
            {"section": "kpi_pending_activities", "label": "Pending Activities", "value": activities.filter(status=models.StatusChoices.PLANNED).count(), "icon": "bi-hourglass", "color": "warning"},
            {"section": "kpi_present_workers", "label": "Present Workers", "value": attendance_today.filter(status="PRESENT").count(), "icon": "bi-person-check", "color": "success"},
            {"section": "kpi_absent_workers", "label": "Absent Workers", "value": attendance_today.filter(status="ABSENT").count(), "icon": "bi-person-x", "color": "danger"},
            {"section": "kpi_material_received", "label": "Material Received Today", "value": int(transactions.filter(transaction_type="RECEIVED").aggregate(total=Sum("quantity"))["total"] or 0), "icon": "bi-box-arrow-in-down", "color": "info"},
            {"section": "kpi_material_consumed", "label": "Material Consumed Today", "value": int(transactions.filter(transaction_type="CONSUMED").aggregate(total=Sum("quantity"))["total"] or 0), "icon": "bi-box-arrow-up", "color": "warning"},
            {"section": "kpi_pending_dpr", "label": "Pending DPR", "value": models.DailyProgressReport.objects.filter(status=models.StatusChoices.PLANNED).count(), "icon": "bi-file-earmark-text", "color": "secondary"},
            {"section": "kpi_open_issues", "label": "Open Site Issues", "value": models.SiteIssue.objects.filter(status=models.StatusChoices.ACTIVE).count(), "icon": "bi-exclamation-circle", "color": "danger"},
            {"section": "kpi_safety_alerts", "label": "Safety Alerts", "value": models.SafetyInspection.objects.filter(status=models.StatusChoices.DELAYED).count(), "icon": "bi-shield-exclamation", "color": "danger"},
        ],
        "assigned_sites": sites[:6],
        "activities": activities.order_by("-start_date")[:6],
        "recent_photos": models.ConstructionPhoto.objects.all()[:6],
        "pending_tasks": activities.filter(status=models.StatusChoices.PLANNED)[:5],
        "issue_alerts": models.SiteIssue.objects.filter(status=models.StatusChoices.ACTIVE)[:5],
        "progress_chart": _chart_json({
            "labels": [d["label"] for d in progress_days],
            "values": [d["value"] for d in progress_days],
        }),
    }
    return render(request, "ConstructionManagement/site_supervisor/dashboard.html", context)


def supervisor_page(request, page):
    if page == "dashboard":
        return supervisor_dashboard(request)
    if page == "reports":
        return reports(request, "supervisor")
    if page == "settings":
        return settings_page(request, "supervisor")
    if page == "notifications":
        return resource_list(request, "supervisor", "notification", page_title="Notifications")
    if page in SUPERVISOR_PAGES:
        qs = None
        if page == "receiving":
            qs = models.MaterialTransaction.objects.filter(transaction_type="RECEIVED")
        elif page == "materials":
            qs = models.Material.objects.all()
        return resource_list(request, "supervisor", SUPERVISOR_PAGES[page], queryset=qs)
    messages.error(request, "The requested page does not exist.")
    return redirect("supervisor_dashboard")
