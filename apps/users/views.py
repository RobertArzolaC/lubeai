from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
    View,
)
from django_filters.views import FilterView

from apps.core import mixins as core_mixins
from apps.users import filtersets, forms, models


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Profile")
        context["back_url"] = reverse_lazy("apps.dashboard:index")

        return context


class SettingsView(SuccessMessageMixin, LoginRequiredMixin, View):
    template_name = "users/settings.html"
    success_message = _("Settings updated successfully")
    success_url = reverse_lazy("apps.users:settings")

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = {
            "entity": _("Settings"),
            "back_url": reverse_lazy("apps.dashboard:index"),
            "user_form": forms.UserSettingsForm(instance=user),
        }

        if user.is_account:
            context["account_form"] = forms.AccountSettingsForm(
                instance=user.account
            )

        context.update(kwargs)
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        try:
            user = request.user

            user_form = forms.UserSettingsForm(
                request.POST, request.FILES, instance=user
            )
            if user_form.is_valid():
                user_form.save()

            if user.is_account:
                customer_form = forms.AccountSettingsForm(
                    request.POST, request.FILES, instance=user.account
                )

                if customer_form.is_valid():
                    customer_form.save()

            messages.success(request, self.success_message)
            return redirect(self.success_url)
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")

        return render(request, self.template_name, self.get_context_data())


class AccountListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Account
    permission_required = "users.view_account"
    filterset_class = filtersets.AccountFilter
    template_name = "users/account/list.html"
    context_object_name = "accounts"
    paginate_by = 5

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(Q(user__is_staff=True) | Q(user__is_superuser=True))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["entity_plural"] = _("Accounts")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy("apps.users:account_create")

        return context


class AccountCreateView(
    PermissionRequiredMixin, FormView, LoginRequiredMixin, SuccessMessageMixin
):
    form_class = forms.AccountCreationForm
    permission_required = "users.add_account"
    template_name = "users/account/form.html"
    success_message = _("Account created successfully")
    success_url = reverse_lazy("apps.users:account_list")

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["back_url"] = reverse_lazy("apps.users:account_list")
        return context


class AccountUpdateView(
    PermissionRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = models.Account
    context_object_name = "account"
    form_class = forms.AccountUpdateForm
    template_name = "users/account/form.html"
    permission_required = "users.change_account"
    success_message = _("Account updated successfully")
    success_url = reverse_lazy("apps.users:account_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["back_url"] = reverse_lazy("apps.users:account_list")
        return context


class AccountDeleteView(core_mixins.AjaxDeleteViewMixin):
    model = models.Account


# =====================================
# Organization Views
# =====================================


class OrganizationListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Organization
    permission_required = "users.view_organization"
    filterset_class = filtersets.OrganizationFilter
    template_name = "users/organization/list.html"
    context_object_name = "organizations"
    ordering = ["is_active", "name"]
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Organization")
        context["entity_plural"] = _("Organizations")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy(
            "apps.users:organization_create"
        )

        return context


class OrganizationDetailView(
    PermissionRequiredMixin, DetailView, LoginRequiredMixin
):
    model = models.Organization
    permission_required = "users.view_organization"
    template_name = "users/organization/detail.html"
    context_object_name = "organization"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Organization")
        context["back_url"] = reverse_lazy("apps.users:organization_list")
        context["edit_url"] = reverse_lazy(
            "apps.users:organization_update", kwargs={"pk": self.object.pk}
        )
        return context


class OrganizationCreateView(
    PermissionRequiredMixin, CreateView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Organization
    form_class = forms.OrganizationForm
    permission_required = "users.add_organization"
    template_name = "users/organization/form.html"
    success_message = _("Organization created successfully")
    success_url = reverse_lazy("apps.users:organization_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Organization")
        context["back_url"] = reverse_lazy("apps.users:organization_list")
        return context


class OrganizationUpdateView(
    PermissionRequiredMixin, UpdateView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Organization
    form_class = forms.OrganizationForm
    template_name = "users/organization/form.html"
    permission_required = "users.change_organization"
    success_message = _("Organization updated successfully")
    success_url = reverse_lazy("apps.users:organization_list")
    context_object_name = "organization"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Organization")
        context["back_url"] = reverse_lazy("apps.users:organization_list")
        return context


class OrganizationDeleteView(core_mixins.AjaxDeleteViewMixin):
    model = models.Organization
