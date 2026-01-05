"""Reports views."""

import openpyxl
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    UpdateView,
    View,
)
from django_filters.views import FilterView
from openpyxl.styles import Font

from apps.core import mixins as core_mixins
from apps.equipment import models as equipment_models
from apps.reports import filtersets, forms, models
from apps.users import models as users_models


class ReportListView(
    PermissionRequiredMixin,
    FilterView,
    LoginRequiredMixin,
):
    """List view for reports."""

    model = models.Report
    permission_required = "reports.view_report"
    filterset_class = filtersets.ReportFilter
    template_name = "reports/report/list.html"
    context_object_name = "reports"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Report")
        context["entity_plural"] = _("Reports")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy("apps.reports:report_create")
        context["bulk_upload_url"] = reverse_lazy(
            "apps.reports:report_bulk_upload"
        )
        return context


class ReportDetailView(
    PermissionRequiredMixin,
    DetailView,
    LoginRequiredMixin,
):
    """Detail view for report."""

    model = models.Report
    permission_required = "reports.view_report"
    template_name = "reports/report/detail.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Report")
        context["back_url"] = reverse_lazy("apps.reports:report_list")
        context["edit_url"] = reverse_lazy(
            "apps.reports:report_update", kwargs={"pk": self.object.pk}
        )
        return context


class ReportCreateView(
    PermissionRequiredMixin,
    CreateView,
    LoginRequiredMixin,
    SuccessMessageMixin,
):
    """Create view for report."""

    model = models.Report
    form_class = forms.ReportForm
    permission_required = "reports.add_report"
    template_name = "reports/report/form.html"
    success_message = _("Report created successfully")
    success_url = reverse_lazy("apps.reports:report_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Report")
        context["back_url"] = reverse_lazy("apps.reports:report_list")
        context["form_title"] = _("Create Report")
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ReportUpdateView(
    PermissionRequiredMixin,
    UpdateView,
    LoginRequiredMixin,
    SuccessMessageMixin,
):
    """Update view for report."""

    model = models.Report
    form_class = forms.ReportForm
    permission_required = "reports.change_report"
    template_name = "reports/report/form.html"
    success_message = _("Report updated successfully")
    success_url = reverse_lazy("apps.reports:report_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Report")
        context["back_url"] = reverse_lazy("apps.reports:report_list")
        context["form_title"] = _("Edit Report")
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ReportDeleteView(core_mixins.AjaxDeleteViewMixin):
    """Delete view for report."""

    model = models.Report


class ReportBulkUploadView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    SuccessMessageMixin,
    FormView,
):
    """Bulk upload view for reports."""

    permission_required = "reports.add_report"
    form_class = forms.ReportBulkUploadForm
    template_name = "reports/report/bulk_upload.html"
    success_url = reverse_lazy("apps.reports:report_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Report")
        context["entity_plural"] = _("Reports")
        context["back_url"] = reverse_lazy("apps.reports:report_list")
        context["template_url"] = reverse_lazy(
            "apps.reports:report_bulk_template"
        )
        return context

    def form_valid(self, form):
        excel_file = form.cleaned_data["file"]
        try:
            results = self._process_excel_file(excel_file)
            self._show_results_messages(results)
        except Exception as e:
            messages.error(
                self.request,
                _("Error processing file: %(error)s") % {"error": str(e)},
            )
        return super().form_valid(form)

    def _process_excel_file(self, excel_file):
        """Process Excel file and create/update reports."""
        results = {"created": 0, "updated": 0, "errors": [], "skipped": 0}

        try:
            workbook = openpyxl.load_workbook(excel_file)
            worksheet = workbook.active

            for row_num, row in enumerate(
                worksheet.iter_rows(min_row=3, values_only=True), start=3
            ):
                # Skip empty rows
                if not any(row):
                    continue

                # Skip title/header rows
                if self._is_title_or_header_row(row):
                    results["skipped"] += 1
                    continue

                try:
                    with transaction.atomic():
                        result = self._process_row(row, row_num)
                        if result == "created":
                            results["created"] += 1
                        elif result == "updated":
                            results["updated"] += 1
                except ValidationError as e:
                    results["errors"].append(f"Row {row_num}: {e.message}")
                except Exception as e:
                    results["errors"].append(f"Row {row_num}: {str(e)}")

        finally:
            workbook.close()

        return results

    def _is_title_or_header_row(self, row):
        """Check if row is a title or header row."""
        if not row or not row[0]:
            return True

        first_cell = str(row[0]).upper()
        # Skip common title/header patterns
        title_patterns = [
            "REPORTE",
            "REPORT",
            "LAB",
            "LABORATORIO",
            "LABORATORY",
            "NUMERO",
            "NUMBER",
        ]

        return any(pattern in first_cell for pattern in title_patterns)

    def _process_row(self, row, row_num):
        """Process a single row from Excel."""
        # Expected columns based on template
        (
            lab_number,
            organization_name,
            machine_name,
            component_name,
            lubricant,
            lubricant_hours_kms,
            serial_number_code,
            sample_date,
            per_number,
            reception_date,
            status,
            condition,
            notes,
        ) = row[:13]

        # Validate required fields
        if not lab_number:
            raise ValidationError(_("Lab Number is required"))

        # Get or create related objects
        organization = None
        if organization_name:
            try:
                organization = users_models.Organization.objects.get(
                    name__iexact=organization_name, is_active=True
                )
            except users_models.Organization.DoesNotExist:
                raise ValidationError(
                    _("Organization '%(name)s' not found")
                    % {"name": organization_name}
                )

        machine = None
        if machine_name:
            try:
                machine = equipment_models.Machine.objects.get(
                    name__iexact=machine_name, is_active=True
                )
            except equipment_models.Machine.DoesNotExist:
                raise ValidationError(
                    _("Machine '%(name)s' not found") % {"name": machine_name}
                )

        component = None
        if component_name:
            try:
                component = equipment_models.Component.objects.get(
                    name__iexact=component_name, is_active=True
                )
            except equipment_models.Component.DoesNotExist:
                raise ValidationError(
                    _("Component '%(name)s' not found")
                    % {"name": component_name}
                )

        # Create or update report
        report, created = models.Report.objects.update_or_create(
            lab_number=lab_number,
            defaults={
                "organization": organization,
                "machine": machine,
                "component": component,
                "lubricant": lubricant or "",
                "lubricant_hours_kms": lubricant_hours_kms,
                "serial_number_code": serial_number_code or "",
                "sample_date": sample_date,
                "per_number": per_number or "",
                "reception_date": reception_date,
                "status": status or models.choices.ReportStatus.PENDING,
                "condition": condition or models.choices.ReportCondition.NORMAL,
                "notes": notes or "",
                "is_active": True,
                "created_by": self.request.user,
                "modified_by": self.request.user,
            },
        )

        return "created" if created else "updated"

    def _show_results_messages(self, results):
        """Show result messages to user."""
        if results["created"]:
            messages.success(
                self.request,
                _("Successfully created %(count)d reports")
                % {"count": results["created"]},
            )

        if results["updated"]:
            messages.info(
                self.request,
                _("Successfully updated %(count)d reports")
                % {"count": results["updated"]},
            )

        if results["skipped"]:
            messages.info(
                self.request,
                _("Skipped %(count)d header/title rows")
                % {"count": results["skipped"]},
            )

        if results["errors"]:
            for error in results["errors"]:
                messages.error(self.request, error)


class ReportBulkTemplateView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    View,
):
    """Generate Excel template for bulk upload."""

    permission_required = "reports.add_report"

    def get(self, request, *args, **kwargs):
        """Generate and return Excel template."""
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Reports Template"

        # Add title
        worksheet.merge_cells("A1:M1")
        worksheet["A1"] = "REPORTE DE REPORTES - TEMPLATE"
        worksheet["A1"].font = Font(bold=True, size=14)

        # Add headers
        headers = [
            "Lab Number *",
            "Organization",
            "Machine",
            "Component",
            "Lubricant",
            "Lubricant Hours/Kms",
            "Serial Number Code",
            "Sample Date",
            "PER Number",
            "Reception Date",
            "Status",
            "Condition",
            "Notes",
        ]

        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=2, column=col, value=header)
            cell.font = Font(bold=True)

        # Add example data
        example_data = [
            "LAB001",
            "Acme Corp",
            "Engine 001",
            "Motor",
            "Shell Oil",
            "1000",
            "SN123456",
            "2024-01-01",
            "PER001",
            "2024-01-02",
            "PENDING",
            "NORMAL",
            "Example notes",
        ]

        for col, value in enumerate(example_data, 1):
            worksheet.cell(row=3, column=col, value=value)

        # Set column widths
        column_widths = [15, 20, 20, 15, 15, 18, 18, 15, 15, 15, 12, 12, 25]
        for col, width in enumerate(column_widths, 1):
            worksheet.column_dimensions[
                openpyxl.utils.get_column_letter(col)
            ].width = width

        # Generate response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            'attachment; filename="report_bulk_template.xlsx"'
        )

        workbook.save(response)
        workbook.close()
        return response
