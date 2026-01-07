import django_filters
from django.utils.translation import gettext_lazy as _

from apps.equipment import models as equipment_models
from apps.reports import choices, models
from apps.users import models as users_models


class DashboardReportFilter(django_filters.FilterSet):
    """Filter for dashboard reports."""

    organization = django_filters.ModelChoiceFilter(
        queryset=users_models.Organization.objects.filter(
            is_active=True, is_removed=False
        ),
        empty_label=_("All Organizations"),
        label=_("Organization"),
    )
    start_date = django_filters.DateFilter(
        field_name="sample_date",
        lookup_expr="gte",
        label=_("Start Date"),
    )
    end_date = django_filters.DateFilter(
        field_name="sample_date",
        lookup_expr="lte",
        label=_("End Date"),
    )
    machine = django_filters.ModelChoiceFilter(
        queryset=equipment_models.Machine.objects.filter(is_active=True),
        empty_label=_("All Machines"),
        label=_("Machine"),
    )
    condition = django_filters.ChoiceFilter(
        field_name="condition",
        empty_label=_("All Conditions"),
        choices=choices.ReportCondition.choices,
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        empty_label=_("All Statuses"),
        choices=choices.ReportStatus.choices,
    )

    class Meta:
        model = models.Report
        fields = [
            "organization",
            "start_date",
            "end_date",
            "machine",
            "condition",
            "status",
        ]
