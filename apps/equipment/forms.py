"""Equipment forms."""

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.equipment import models


class MachineForm(forms.ModelForm):
    class Meta:
        model = models.Machine
        fields = [
            "organization",
            "name",
            "serial_number",
            "model",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class ComponentForm(forms.ModelForm):
    class Meta:
        model = models.Component
        fields = [
            "type",
            "serial_number",
            "installation_datetime",
            "is_active",
        ]
        widgets = {
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "installation_datetime": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].queryset = models.ComponentType.objects.filter(
            is_active=True
        )
        self.fields["type"].empty_label = _("Select Component Type")


ComponentFormSet = inlineformset_factory(
    models.Machine,
    models.Component,
    form=ComponentForm,
    extra=1,
    can_delete=True,
)


class MachineBulkUploadForm(forms.Form):
    """Form for bulk uploading machines from Excel file."""

    file = forms.FileField(
        label=_("Excel File"),
        help_text=_("Upload an Excel file (.xlsx) with machine data"),
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".xlsx",
            }
        ),
    )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get("file")

        if file:
            # Check file extension
            if not file.name.lower().endswith(".xlsx"):
                raise forms.ValidationError(_("Only .xlsx files are allowed"))

            # Check file size (5MB max)
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(_("File size cannot exceed 5MB"))

        return file
