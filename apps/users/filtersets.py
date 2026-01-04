import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.users import models


class AccountFilter(django_filters.FilterSet):
    name_search = django_filters.CharFilter(
        method="filter_by_name", label=_("Search")
    )
    is_active = django_filters.ChoiceFilter(
        field_name="user__is_active",
        empty_label=_("Is Active?"),
        label=_("Status"),
        choices=(
            (True, _("Active")),
            (False, _("Inactive")),
        ),
    )

    class Meta:
        model = models.Account
        fields = ["name_search", "is_active"]

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(user__first_name__icontains=value)  # noqa
            | Q(user__last_name__icontains=value)  # noqa
            | Q(user__email__icontains=value)  # noqa
        )


class OrganizationFilter(django_filters.FilterSet):
    name_search = django_filters.CharFilter(
        method="filter_by_name", label=_("Search")
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
        model = models.Organization
        fields = ["name_search", "is_active"]

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(email__icontains=value)
            | Q(phone__icontains=value)
        )
