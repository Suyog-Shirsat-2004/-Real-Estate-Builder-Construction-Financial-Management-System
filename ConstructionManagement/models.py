"""Database models for the Real Estate Builder construction management system."""

from django.db import models


class StatusChoices(models.TextChoices):
    PLANNED = "PLANNED", "Planned"
    ACTIVE = "ACTIVE", "Active"
    ON_HOLD = "ON_HOLD", "On Hold"
    COMPLETED = "COMPLETED", "Completed"
    DELAYED = "DELAYED", "Delayed"
    CANCELLED = "CANCELLED", "Cancelled"


class PriorityChoices(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class Project(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    client = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    progress = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)
    manager = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Site(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sites")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=40, unique=True)
    location = models.CharField(max_length=200, blank=True)
    area_sqft = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    expected_completion = models.DateField(null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    supervisor = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Contractor(models.Model):
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    specialty = models.CharField(max_length=120, blank=True)
    contract_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Activity(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="activities")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activities", null=True, blank=True)
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, related_name="activities", null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    activity_type = models.CharField(max_length=80, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)
    assigned_to = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-start_date", "title"]
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.title


class Material(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, default="pcs")
    quantity_in_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier = models.CharField(max_length=150, blank=True)
    last_restocked = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_low(self):
        return self.quantity_in_stock <= self.reorder_level


class MaterialRequest(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="material_requests")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="requests")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    requested_by = models.CharField(max_length=120, blank=True)
    request_date = models.DateField(null=True, blank=True)
    needed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-request_date"]

    def __str__(self):
        return f"{self.material.name} - {self.site.name}"


class MaterialTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("RECEIVED", "Received"),
        ("CONSUMED", "Consumed"),
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="material_transactions")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default="RECEIVED")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    recorded_by = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.material.name}"


class Labour(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="labour", null=True, blank=True)
    worker_id = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    daily_wage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    join_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Labour"

    def __str__(self):
        return f"{self.worker_id} - {self.name}"


class Attendance(models.Model):
    ATTENDANCE_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("HALF_DAY", "Half Day"),
    )

    labour = models.ForeignKey(Labour, on_delete=models.CASCADE, related_name="attendance")
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="attendance", null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES, default="PRESENT")
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["labour", "date"], name="unique_labour_attendance_date"),
        ]

    def __str__(self):
        return f"{self.labour.name} - {self.date} - {self.status}"


class Budget(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="budgets")
    category = models.CharField(max_length=120)
    allocated = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    month = models.PositiveSmallIntegerField(default=1)
    year = models.PositiveIntegerField(default=2026)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-year", "-month", "category"]

    def __str__(self):
        return f"{self.project.name} - {self.category}"

    @property
    def utilization(self):
        if not self.allocated:
            return 0
        return round(float(self.spent / self.allocated) * 100, 1)


class Expense(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="expenses")
    budget = models.ForeignKey(Budget, on_delete=models.SET_NULL, related_name="expenses", null=True, blank=True)
    category = models.CharField(max_length=120)
    description = models.CharField(max_length=250, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    approved_by = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.category} - {self.amount}"


class DailyProgressReport(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="dprs")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="dprs", null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)
    work_completed = models.TextField(blank=True)
    labour_count = models.PositiveIntegerField(default=0)
    material_used = models.TextField(blank=True)
    issues = models.TextField(blank=True)
    weather = models.CharField(max_length=80, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    submitted_by = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    verified_by = models.CharField(max_length=120, blank=True)
    verified_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Daily Progress Report"
        verbose_name_plural = "Daily Progress Reports"

    def __str__(self):
        return f"DPR {self.date} - {self.site.name}"


class ProjectMilestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return self.title


class QualityInspection(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="quality_inspections")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="quality_inspections", null=True, blank=True)
    inspection_date = models.DateField(null=True, blank=True)
    inspector = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=150, blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    class Meta:
        ordering = ["-inspection_date"]

    def __str__(self):
        return f"Quality - {self.area} ({self.site.name})"


class SafetyInspection(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="safety_inspections")
    inspection_date = models.DateField(null=True, blank=True)
    inspector = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=150, blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    class Meta:
        ordering = ["-inspection_date"]

    def __str__(self):
        return f"Safety - {self.area} ({self.site.name})"


class SiteIssue(models.Model):
    SEVERITY_CHOICES = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="issues")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="MEDIUM")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    reported_by = models.CharField(max_length=120, blank=True)
    reported_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    resolution = models.TextField(blank=True)

    class Meta:
        ordering = ["-reported_date"]

    def __str__(self):
        return self.title


class ConstructionPhoto(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="photos")
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="constructionphotos/")
    caption = models.TextField(blank=True)
    taken_at = models.DateField(null=True, blank=True)
    uploaded_by = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self):
        return self.title


class Notification(models.Model):
    AUDIENCE_CHOICES = (
        ("ALL", "Everyone"),
        ("MANAGER", "Site Manager"),
        ("SUPERVISOR", "Site Supervisor"),
    )

    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    audience = models.CharField(max_length=15, choices=AUDIENCE_CHOICES, default="ALL")
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
