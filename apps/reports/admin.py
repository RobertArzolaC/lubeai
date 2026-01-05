"""Reports admin configuration."""

from django.contrib import admin

from apps.reports.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin configuration for Report model."""

    list_display = (
        "lab_number",
        "organization",
        "machine",
        "lubricant",
        "sample_date",
        "reception_date",
        "status",
        "condition",
        "is_active",
    )
    list_filter = (
        "status",
        "condition",
        "is_active",
        "organization",
        "sample_date",
        "reception_date",
    )
    search_fields = (
        "lab_number",
        "per_number",
        "serial_number_code",
        "lubricant",
        "organization__name",
        "machine__name",
    )
    readonly_fields = ("created", "modified", "created_by", "modified_by")
    date_hierarchy = "sample_date"
    ordering = ("-sample_date", "-created")
    raw_id_fields = ("organization", "machine", "component")
