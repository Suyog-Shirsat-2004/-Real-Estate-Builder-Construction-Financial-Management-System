"""ModelForms used by the construction management modules."""

from django import forms
from django.utils import timezone

from . import models


def make_model_form(model, fields):
    """Create a Bootstrap-friendly ModelForm for a model and field list."""
    widgets = {}
    for field_name in fields:
        field = model._meta.get_field(field_name)
        internal = field.get_internal_type()
        if field.is_relation:
            widgets[field_name] = forms.Select(attrs={"class": "form-select"})
        elif internal == "DateField":
            widgets[field_name] = forms.DateInput(attrs={"type": "date", "class": "form-control"})
        elif internal == "DateTimeField":
            widgets[field_name] = forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"})
        elif internal == "TimeField":
            widgets[field_name] = forms.TimeInput(attrs={"type": "time", "class": "form-control"})
        elif internal == "TextField":
            widgets[field_name] = forms.Textarea(attrs={"class": "form-control", "rows": 3})
        elif internal == "BooleanField":
            widgets[field_name] = forms.CheckboxInput(attrs={"class": "form-check-input"})
        elif internal in ("IntegerField", "PositiveIntegerField", "PositiveSmallIntegerField", "DecimalField", "FloatField"):
            widgets[field_name] = forms.NumberInput(attrs={"class": "form-control", "step": "any"})
        elif internal == "EmailField":
            widgets[field_name] = forms.EmailInput(attrs={"class": "form-control"})
        elif internal in ("FileField", "ImageField"):
            widgets[field_name] = forms.ClearableFileInput(attrs={"class": "form-control"})
        else:
            widgets[field_name] = forms.TextInput(attrs={"class": "form-control"})

    model_cls = model
    field_list = fields
    widget_map = widgets

    class DynamicModelForm(forms.ModelForm):
        class Meta:
            model = model_cls
            fields = field_list
            widgets = widget_map

    DynamicModelForm.__name__ = f"{model.__name__}Form"
    return DynamicModelForm


FORM_SPECS = {
    "project": (models.Project, ["name", "code", "description", "client", "location", "start_date", "end_date", "budget", "progress", "status", "priority", "manager"]),
    "site": (models.Site, ["project", "name", "code", "location", "area_sqft", "start_date", "expected_completion", "progress", "status", "supervisor", "description"]),
    "contractor": (models.Contractor, ["name", "company", "contact_person", "phone", "email", "specialty", "contract_value", "start_date", "end_date", "rating", "status"]),
    "activity": (models.Activity, ["site", "project", "contractor", "title", "description", "activity_type", "start_date", "end_date", "progress", "status", "priority", "assigned_to"]),
    "material": (models.Material, ["name", "category", "unit", "quantity_in_stock", "reorder_level", "unit_cost", "supplier", "last_restocked"]),
    "material_request": (models.MaterialRequest, ["site", "material", "quantity", "requested_by", "request_date", "needed_date", "status", "remarks"]),
    "material_transaction": (models.MaterialTransaction, ["site", "material", "transaction_type", "quantity", "date", "reference", "recorded_by", "notes"]),
    "labour": (models.Labour, ["site", "worker_id", "name", "role", "phone", "daily_wage", "join_date", "status"]),
    "attendance": (models.Attendance, ["labour", "site", "date", "status", "check_in", "check_out", "remarks"]),
    "budget": (models.Budget, ["project", "category", "allocated", "spent", "month", "year", "notes"]),
    "expense": (models.Expense, ["project", "budget", "category", "description", "amount", "date", "vendor", "status", "approved_by"]),
    "dpr": (models.DailyProgressReport, ["site", "project", "date", "summary", "work_completed", "labour_count", "material_used", "issues", "weather", "progress_percentage", "submitted_by", "status", "verified_by", "verified_date"]),
    "milestone": (models.ProjectMilestone, ["project", "title", "description", "due_date", "progress", "status"]),
    "quality": (models.QualityInspection, ["site", "project", "inspection_date", "inspector", "area", "score", "status", "findings", "recommendations"]),
    "safety": (models.SafetyInspection, ["site", "inspection_date", "inspector", "area", "score", "status", "findings", "recommendations"]),
    "issue": (models.SiteIssue, ["site", "title", "description", "severity", "status", "reported_by", "reported_date", "resolved_date", "resolution"]),
    "photo": (models.ConstructionPhoto, ["site", "title", "image", "caption", "taken_at", "uploaded_by"]),
    "notification": (models.Notification, ["title", "message", "category", "audience", "is_read", "link"]),
}

FORMS = {key: make_model_form(model, fields) for key, (model, fields) in FORM_SPECS.items()}


class AttendanceForm(forms.ModelForm):
    """Simple attendance entry: one record per worker per date.

    Selecting a worker and date that already exists updates that record instead
    of failing with a duplicate error, which makes daily attendance quick to mark.
    """

    class Meta:
        model = models.Attendance
        fields = ["labour", "site", "date", "status", "check_in", "check_out", "remarks"]
        widgets = {
            "labour": forms.Select(attrs={"class": "form-select"}),
            "site": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "check_in": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "check_out": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = timezone.localdate()
        self.fields["status"].initial = "PRESENT"
        self.fields["status"].required = False
        self.fields["labour"].empty_label = "Select a worker"
        self.fields["site"].empty_label = "Auto-filled from worker"
        self.fields["labour"].help_text = "One attendance record per worker per date."
        self.fields["site"].help_text = "Optional — taken from the selected worker automatically."
        self.fields["status"].help_text = "Defaults to Present."

    def clean(self):
        cleaned = super().clean()
        labour = cleaned.get("labour")
        day = cleaned.get("date") or timezone.localdate()
        cleaned["date"] = day
        cleaned["status"] = cleaned.get("status") or "PRESENT"

        if not cleaned.get("site") and labour:
            cleaned["site"] = labour.site

        if labour and day:
            existing = models.Attendance.objects.filter(labour=labour, date=day)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            duplicate = existing.first()
            if duplicate:
                if self.instance.pk:
                    self._duplicate_error = True
                    raise forms.ValidationError(
                        f"Another attendance record already exists for {labour.name} on {day}. "
                        "Choose a different worker or date."
                    )
                # Add mode: update the existing entry rather than rejecting the form.
                self.instance = duplicate
                self.success_message = f"Attendance for {labour.name} on {day} was updated successfully."

        return cleaned

    def validate_unique(self):
        # Avoid a second, generic message when clean() already reported the clash.
        if getattr(self, "_duplicate_error", False):
            return
        super().validate_unique()

    def validate_constraints(self):
        # Django also validates Meta.constraints separately from unique fields.
        if getattr(self, "_duplicate_error", False):
            return
        super().validate_constraints()


FORMS["attendance"] = AttendanceForm


class PhotoForm(forms.ModelForm):
    """Photo upload with date, time and uploader filled in automatically."""

    class Meta:
        model = models.ConstructionPhoto
        fields = ["site", "title", "image", "caption", "taken_at", "uploaded_by"]
        widgets = {
            "site": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "caption": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "taken_at": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "uploaded_by": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, module=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_uploader = "Site Manager" if module == "manager" else "Site Supervisor"
        self.fields["taken_at"].initial = timezone.localdate()
        self.fields["uploaded_by"].initial = self.default_uploader
        self.fields["taken_at"].help_text = "Defaults to today."
        self.fields["uploaded_by"].help_text = "Filled in automatically — editable."

    def clean(self):
        cleaned = super().clean()
        cleaned["taken_at"] = cleaned.get("taken_at") or timezone.localdate()
        cleaned["uploaded_by"] = cleaned.get("uploaded_by") or self.default_uploader
        return cleaned


FORMS["photo"] = PhotoForm


class SearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search records..."}))
    status = forms.ChoiceField(required=False, choices=[("", "All statuses")] + list(models.StatusChoices.choices), widget=forms.Select(attrs={"class": "form-select"}))
