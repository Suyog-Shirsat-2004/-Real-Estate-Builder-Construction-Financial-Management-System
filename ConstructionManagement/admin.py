from django.contrib import admin

from . import models

for model in [
    models.Project, models.Site, models.Contractor, models.Activity,
    models.Material, models.MaterialRequest, models.MaterialTransaction,
    models.Labour, models.Attendance, models.Budget, models.Expense,
    models.DailyProgressReport, models.ProjectMilestone,
    models.QualityInspection, models.SafetyInspection, models.SiteIssue,
    models.ConstructionPhoto, models.Notification,
]:
    admin.site.register(model)
