import logging
from datetime import datetime

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
from django.utils.dateparse import parse_date
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

logger = logging.getLogger(__name__)


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
        user_email = self.request.user.email

        logger.info(
            f"Starting bulk upload - User: {user_email}, File: {excel_file.name}"
        )

        try:
            results = self._process_excel_file(excel_file)
            self._show_results_messages(results)
        except Exception as e:
            error_msg = str(e)
            logger.exception(
                f"Bulk upload file processing error - User: {user_email}, "
                f"File: {excel_file.name}, Error: {error_msg}"
            )
            messages.error(
                self.request,
                _("Error processing file: %(error)s") % {"error": error_msg},
            )
        return super().form_valid(form)

    def _process_excel_file(self, excel_file):
        """Process Excel file and create/update reports."""
        results = {"created": 0, "updated": 0, "errors": [], "skipped": 0}
        user_email = self.request.user.email

        logger.debug(
            f"Processing Excel file - User: {user_email}, File: {excel_file.name}"
        )

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
                    error_msg = f"Row {row_num}: {e.message}"
                    results["errors"].append(error_msg)
                    logger.error(
                        f"Bulk upload validation error - User: {user_email}, "
                        f"File: {excel_file.name}, {error_msg}"
                    )
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.exception(
                        f"Bulk upload unexpected error - User: {user_email}, "
                        f"File: {excel_file.name}, {error_msg}"
                    )

        finally:
            workbook.close()

        logger.info(
            f"Finished processing Excel file - User: {user_email}, "
            f"File: {excel_file.name}, Created: {results['created']}, "
            f"Updated: {results['updated']}, Skipped: {results['skipped']}, "
            f"Errors: {len(results['errors'])}"
        )

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
                    organization=organization,
                    name__iexact=machine_name,
                    is_active=True,
                )
            except equipment_models.Machine.DoesNotExist:
                logger.debug(
                    f"Machine lookup failed - Row {row_num}, "
                    f"Machine: {machine_name}, Organization: {organization_name}"
                )
                raise ValidationError(
                    _("Machine '%(name)s' not found") % {"name": machine_name}
                )
            except equipment_models.Machine.MultipleObjectsReturned:
                logger.debug(
                    f"Multiple machines found - Row {row_num}, "
                    f"Machine: {machine_name}, Organization: {organization_name}"
                )
                raise ValidationError(
                    _("Multiple machines found with name '%(name)s'")
                    % {"name": machine_name}
                )

        component = None
        if component_name:
            try:
                component_name = component_name.replace("  ", " ").strip()
                component = equipment_models.Component.objects.get(
                    machine=machine,
                    type__name__iexact=component_name,
                    is_active=True,
                )
            except equipment_models.Component.DoesNotExist:
                logger.debug(
                    f"Component lookup failed - Row {row_num}, "
                    f"Component: {component_name}, Machine: {machine_name}, "
                    f"Organization: {organization_name}"
                )
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
                "lubricant_hours_kms": self._parse_number(lubricant_hours_kms),
                "serial_number_code": serial_number_code or "",
                "sample_date": self._parse_date(sample_date),
                "per_number": per_number or "",
                "reception_date": self._parse_date(reception_date),
                "status": self._parse_status(status),
                "condition": condition or models.choices.ReportCondition.NORMAL,
                "notes": notes or "",
                "is_active": True,
                "created_by": self.request.user,
                "modified_by": self.request.user,
            },
        )

        return "created" if created else "updated"

    def _parse_status(self, status_value):
        """Parse status value to valid ReportStatus choice."""
        if not status_value:
            return models.choices.ReportStatus.PENDING

        options = dict(
            pendiente="PENDING",
            revisado="REVIEWED",
            aprobado="APPROVED",
            rechazado="REJECTED",
        )
        status_key = str(status_value).strip().lower()
        if status_key in options:
            return options[status_key]

        return models.choices.ReportStatus.PENDING

    def _parse_number(self, number_value):
        """Parse number value to integer or float."""
        if "-" in str(number_value):
            return 0

        if "horas" in str(number_value).lower():
            number_value = str(number_value).lower()
            return number_value.replace("horas", "").strip()

        if "km" in str(number_value).lower():
            number_value = str(number_value).lower()
            return number_value.replace("km", "").strip()

        return number_value

    def _parse_date(self, date_string):
        """Parse date string to Django date object."""

        if not date_string:
            return None

        # Convert to string if it's not already
        date_str = str(date_string).strip()

        # Handle common date formats
        date_formats = [
            "%d/%m/%Y",  # 18/12/2025
            "%d-%m-%Y",  # 18-12-2025
            "%Y-%m-%d",  # 2025-12-18 (ISO format)
            "%m/%d/%Y",  # 12/18/2025 (US format)
        ]

        for date_format in date_formats:
            try:
                parsed_datetime = datetime.strptime(date_str, date_format)
                return parsed_datetime.date()
            except ValueError:
                continue

        # Try Django's built-in parser as fallback
        parsed_date = parse_date(date_str)
        if parsed_date:
            return parsed_date

        return None

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

        logger.info(
            f"Bulk upload summary displayed - User: {self.request.user.email}, "
            f"Created: {results['created']}, Updated: {results['updated']}, "
            f"Skipped: {results['skipped']}, Errors: {len(results['errors'])}"
        )


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
