"""Reports forms."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.reports import models


class ReportForm(forms.ModelForm):
    """Form for creating and updating reports."""

    class Meta:
        model = models.Report
        fields = [
            "organization",
            "machine",
            "component",
            "lab_number",
            "lubricant",
            "lubricant_hours",
            "lubricant_kms",
            "serial_number_code",
            "sample_date",
            "per_number",
            "reception_date",
            "status",
            "condition",
            "notes",
            "is_active",
        ]
        widgets = {
            "organization": forms.Select(attrs={"class": "form-select"}),
            "machine": forms.Select(attrs={"class": "form-select"}),
            "component": forms.Select(attrs={"class": "form-select"}),
            "lab_number": forms.TextInput(attrs={"class": "form-control"}),
            "lubricant": forms.TextInput(attrs={"class": "form-control"}),
            "lubricant_hours": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "lubricant_kms": forms.NumberInput(attrs={"class": "form-control"}),
            "serial_number_code": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "sample_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "per_number": forms.TextInput(attrs={"class": "form-control"}),
            "reception_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        self.fields["organization"].required = True
        self.fields["machine"].required = True
        self.fields["component"].required = True
        self.fields["lab_number"].required = True
        self.fields["sample_date"].required = True

        # Filter active related objects
        from apps.equipment import models as equipment_models
        from apps.users import models as users_models

        self.fields[
            "organization"
        ].queryset = users_models.Organization.objects.filter(is_active=True)
        self.fields[
            "machine"
        ].queryset = equipment_models.Machine.objects.filter(is_active=True)
        self.fields[
            "component"
        ].queryset = equipment_models.Component.objects.filter(is_active=True)

    def clean_lab_number(self):
        """Validate that lab_number is unique."""
        lab_number = self.cleaned_data.get("lab_number")
        if lab_number:
            # Check for existing lab_number excluding current instance
            qs = models.Report.objects.filter(lab_number=lab_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    _("A report with this lab number already exists.")
                )
        return lab_number


class ReportBulkUploadForm(forms.Form):
    """Form for bulk uploading reports from Excel file."""

    file = forms.FileField(
        label=_("Excel File"),
        help_text=_(
            "Upload an Excel file (.xlsx) with report data. Maximum size: 5MB"
        ),
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".xlsx,.xls"}
        ),
    )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get("file")
        if file:
            # Check file extension
            if not file.name.lower().endswith((".xlsx", ".xls")):
                raise ValidationError(
                    _("Only Excel files (.xlsx, .xls) are allowed.")
                )

            # Check file size (5MB max)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_("File size cannot exceed 5MB."))

        return file
