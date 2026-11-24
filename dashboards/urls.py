"""URL patterns for the seven role dashboards."""

from django.urls import path

from . import views

app_name = "dashboards"

urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("builder/", views.builder_dashboard, name="dashboard_builder"),
    path("site-engineer/", views.site_engineer_dashboard, name="dashboard_site_engineer"),
    path("site-supervisor/", views.site_supervisor_dashboard, name="dashboard_site_supervisor"),
    path("contractor/", views.contractor_dashboard, name="dashboard_contractor"),
    path("store-manager/", views.store_manager_dashboard, name="dashboard_store_manager"),
    path("accountant/", views.accountant_dashboard, name="dashboard_accountant"),
    path("labour/", views.labour_dashboard, name="dashboard_labour"),
]
