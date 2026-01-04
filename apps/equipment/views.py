"""Equipment views."""

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from apps.core import mixins as core_mixins
from apps.equipment import filtersets, forms, models


class MachineListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Machine
    permission_required = "equipment.view_machine"
    filterset_class = filtersets.MachineFilter
    template_name = "equipment/machine/list.html"
    context_object_name = "machines"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Machine")
        context["entity_plural"] = _("Machines")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy(
            "apps.equipment:machine_create"
        )
        return context


class MachineDetailView(
    PermissionRequiredMixin, DetailView, LoginRequiredMixin
):
    model = models.Machine
    permission_required = "equipment.view_machine"
    template_name = "equipment/machine/detail.html"
    context_object_name = "machine"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Machine")
        context["back_url"] = reverse_lazy("apps.equipment:machine_list")
        context["edit_url"] = reverse_lazy(
            "apps.equipment:machine_update", kwargs={"pk": self.object.pk}
        )
        context["components"] = self.object.components.select_related("type")
        return context


class MachineCreateView(
    PermissionRequiredMixin, CreateView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Machine
    form_class = forms.MachineForm
    permission_required = "equipment.add_machine"
    template_name = "equipment/machine/form.html"
    success_message = _("Machine created successfully")
    success_url = reverse_lazy("apps.equipment:machine_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Machine")
        context["back_url"] = reverse_lazy("apps.equipment:machine_list")
        if self.request.POST:
            context["component_formset"] = forms.ComponentFormSet(
                self.request.POST
            )
        else:
            context["component_formset"] = forms.ComponentFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        component_formset = context["component_formset"]
        if component_formset.is_valid():
            self.object = form.save()
            component_formset.instance = self.object
            component_formset.save()
            return super().form_valid(form)
        return self.render_to_response(context)


class MachineUpdateView(
    PermissionRequiredMixin, UpdateView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Machine
    form_class = forms.MachineForm
    permission_required = "equipment.change_machine"
    template_name = "equipment/machine/form.html"
    success_message = _("Machine updated successfully")
    success_url = reverse_lazy("apps.equipment:machine_list")
    context_object_name = "machine"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Machine")
        context["back_url"] = reverse_lazy("apps.equipment:machine_list")
        if self.request.POST:
            context["component_formset"] = forms.ComponentFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["component_formset"] = forms.ComponentFormSet(
                instance=self.object
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        component_formset = context["component_formset"]
        if component_formset.is_valid():
            self.object = form.save()
            component_formset.instance = self.object
            component_formset.save()
            return super().form_valid(form)
        return self.render_to_response(context)


class MachineDeleteView(core_mixins.AjaxDeleteViewMixin):
    model = models.Machine
