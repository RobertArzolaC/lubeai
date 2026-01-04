import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.equipment import models
from apps.users.models import Organization


class MachineFilter(django_filters.FilterSet):
    name_search = django_filters.CharFilter(
        method="filter_by_name", label=_("Search")
    )
    organization = django_filters.ModelChoiceFilter(
        queryset=Organization.objects.filter(is_active=True),
        empty_label=_("All Organizations"),
        label=_("Organization"),
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
        model = models.Machine
        fields = ["name_search", "organization", "is_active"]

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(serial_number__icontains=value)
            | Q(model__icontains=value)
        )
