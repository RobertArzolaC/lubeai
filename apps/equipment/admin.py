"""Equipment admin configuration."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.equipment import models


@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    """Admin configuration for Machine model."""

    list_display = (
        "name",
        "serial_number",
        "model",
        "organization",
        "is_active",
        "created",
        "modified",
    )
    list_filter = (
        "is_active",
        "organization",
        "created",
        "modified",
    )
    search_fields = (
        "name",
        "serial_number",
        "model",
        "organization__name",
    )
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "modified_by",
    )

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "serial_number",
                    "model",
                    "organization",
                    "is_active",
                )
            },
        ),
        (
            _("Audit Information"),
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "modified_by",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Override save_model to set created_by and modified_by."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.ComponentType)
class ComponentTypeAdmin(admin.ModelAdmin):
    """Admin configuration for ComponentType model."""

    list_display = (
        "name",
        "is_active",
        "created",
        "modified",
    )
    list_filter = (
        "is_active",
        "created",
        "modified",
    )
    search_fields = (
        "name",
        "description",
    )
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "modified_by",
    )

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            _("Audit Information"),
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "modified_by",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Override save_model to set created_by and modified_by."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Component)
class ComponentAdmin(admin.ModelAdmin):
    """Admin configuration for Component model."""

    list_display = (
        "machine",
        "type",
        "is_active",
        "created",
    )
    list_filter = (
        "is_active",
        "type",
        "created",
    )
    search_fields = (
        "machine__name",
        "machine__serial_number",
        "type__name",
    )
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "modified_by",
    )

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "machine",
                    "type",
                    "is_active",
                )
            },
        ),
        (
            _("Audit Information"),
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "modified_by",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Override save_model to set created_by and modified_by."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
