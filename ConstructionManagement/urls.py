"""URL configuration for the construction management application."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),

    # ---- Site Manager ----
    path("manager/", views.manager_dashboard, name="manager_dashboard"),
    path("manager/details/<str:section>/", views.dashboard_detail, {"module": "manager"}, name="manager_dashboard_detail"),
    path("manager/data/<str:key>/", views.resource_list, {"module": "manager"}, name="manager_crud_list"),
    path("manager/data/<str:key>/add/", views.resource_form, {"module": "manager"}, name="manager_add"),
    path("manager/data/<str:key>/<int:pk>/edit/", views.resource_form, {"module": "manager"}, name="manager_edit"),
    path("manager/data/<str:key>/<int:pk>/delete/", views.resource_delete, {"module": "manager"}, name="manager_delete"),
    path("manager/data/dpr/<int:pk>/verify/", views.verify_dpr, name="verify_dpr"),
    path("manager/data/<str:key>/<int:pk>/", views.resource_detail, {"module": "manager"}, name="manager_detail"),
    path("manager/<str:page>/", views.manager_page, name="manager_page"),

    # ---- Site Supervisor ----
    path("supervisor/", views.supervisor_dashboard, name="supervisor_dashboard"),
    path("supervisor/details/<str:section>/", views.dashboard_detail, {"module": "supervisor"}, name="supervisor_dashboard_detail"),
    path("supervisor/data/<str:key>/", views.resource_list, {"module": "supervisor"}, name="supervisor_crud_list"),
    path("supervisor/data/<str:key>/add/", views.resource_form, {"module": "supervisor"}, name="supervisor_add"),
    path("supervisor/data/<str:key>/<int:pk>/edit/", views.resource_form, {"module": "supervisor"}, name="supervisor_edit"),
    path("supervisor/data/<str:key>/<int:pk>/delete/", views.resource_delete, {"module": "supervisor"}, name="supervisor_delete"),
    path("supervisor/data/<str:key>/<int:pk>/", views.resource_detail, {"module": "supervisor"}, name="supervisor_detail"),
    path("supervisor/<str:page>/", views.supervisor_page, name="supervisor_page"),

    # ---- Named module pages ----
    path("manager/projects/", views.manager_page, {"page": "projects"}, name="manager_projects"),
    path("manager/sites/", views.manager_page, {"page": "sites"}, name="manager_sites"),
    path("manager/activities/", views.manager_page, {"page": "activities"}, name="manager_activities"),
    path("manager/contractors/", views.manager_page, {"page": "contractors"}, name="manager_contractors"),
    path("manager/materials/", views.manager_page, {"page": "materials"}, name="manager_materials"),
    path("manager/labour/", views.manager_page, {"page": "labour"}, name="manager_labour"),
    path("manager/dpr/", views.manager_page, {"page": "dpr"}, name="manager_dpr"),
    path("manager/timeline/", views.manager_page, {"page": "timeline"}, name="manager_timeline"),
    path("manager/finance/", views.manager_page, {"page": "finance"}, name="manager_finance"),
    path("manager/reports/", views.manager_page, {"page": "reports"}, name="manager_reports"),
    path("manager/quality-safety/", views.manager_page, {"page": "quality-safety"}, name="manager_quality_safety"),
    path("manager/notifications/", views.manager_page, {"page": "notifications"}, name="manager_notifications"),
    path("manager/settings/", views.manager_page, {"page": "settings"}, name="manager_settings"),

    path("supervisor/assigned-sites/", views.supervisor_page, {"page": "assigned-sites"}, name="supervisor_assigned_sites"),
    path("supervisor/work-updates/", views.supervisor_page, {"page": "work-updates"}, name="supervisor_work_updates"),
    path("supervisor/attendance/", views.supervisor_page, {"page": "attendance"}, name="supervisor_attendance"),
    path("supervisor/materials/", views.supervisor_page, {"page": "materials"}, name="supervisor_materials"),
    path("supervisor/receiving/", views.supervisor_page, {"page": "receiving"}, name="supervisor_receiving"),
    path("supervisor/photos/", views.supervisor_page, {"page": "photos"}, name="supervisor_photos"),
    path("supervisor/dpr/", views.supervisor_page, {"page": "dpr"}, name="supervisor_dpr"),
    path("supervisor/issues/", views.supervisor_page, {"page": "issues"}, name="supervisor_issues"),
    path("supervisor/quality-checklist/", views.supervisor_page, {"page": "quality-checklist"}, name="supervisor_quality_checklist"),
    path("supervisor/safety-checklist/", views.supervisor_page, {"page": "safety-checklist"}, name="supervisor_safety_checklist"),
    path("supervisor/reports/", views.supervisor_page, {"page": "reports"}, name="supervisor_reports"),
    path("supervisor/notifications/", views.supervisor_page, {"page": "notifications"}, name="supervisor_notifications"),
    path("supervisor/settings/", views.supervisor_page, {"page": "settings"}, name="supervisor_settings"),

    path("notifications/<int:pk>/read/", views.mark_notification_read, name="mark_notification_read"),
]
