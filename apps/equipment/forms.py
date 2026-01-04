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
