"""Reports filtersets."""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.equipment import models as equipment_models
from apps.reports import choices, models
from apps.users import models as users_models


class ReportFilter(django_filters.FilterSet):
    """Filter for reports."""

    lab_number_search = django_filters.CharFilter(
        method="filter_by_lab_number", label=_("Search")
    )
    organization = django_filters.ModelChoiceFilter(
        queryset=users_models.Organization.objects.filter(is_active=True),
        empty_label=_("All Organizations"),
        label=_("Organization"),
    )
    machine = django_filters.ModelChoiceFilter(
        queryset=equipment_models.Machine.objects.filter(is_active=True),
        empty_label=_("All Machines"),
        label=_("Machine"),
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        empty_label=_("All Statuses"),
        label=_("Status"),
        choices=choices.ReportStatus.choices,
    )
    condition = django_filters.ChoiceFilter(
        field_name="condition",
        empty_label=_("All Conditions"),
        label=_("Condition"),
        choices=choices.ReportCondition.choices,
    )
    is_active = django_filters.ChoiceFilter(
        field_name="is_active",
        empty_label=_("Is Active?"),
        label=_("Status"),
        choices=(
            (True, _("Active")),
            (False, _("Inactive")),
        ),
    )

    class Meta:
        model = models.Report
        fields = [
            "lab_number_search",
            "organization",
            "machine",
            "status",
            "condition",
            "is_active",
        ]

    def filter_by_lab_number(self, queryset, name, value):
        """Filter by lab_number, per_number, or serial_number_code."""
        return queryset.filter(
            Q(lab_number__icontains=value)
            | Q(per_number__icontains=value)
            | Q(serial_number_code__icontains=value)
        )
