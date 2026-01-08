from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.core.models import BaseUserTracked, IsActive
from apps.users import models as users_models


class Machine(TimeStampedModel, BaseUserTracked, IsActive):
    """
    Machine model.

    Represents industrial equipment/machinery used for condition monitoring
    and predictive maintenance.
    """

    organization = models.ForeignKey(
        users_models.Organization,
        verbose_name=_("Organization"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="machines",
        help_text=_("Organization that owns this machine"),
    )
    name = models.CharField(
        _("Name"),
        max_length=200,
        help_text=_("Machine name or identifier"),
    )
    serial_number = models.CharField(
        _("Serial Number"),
        max_length=100,
        help_text=_("Unique serial number of the machine"),
    )
    model = models.CharField(
        _("Model"),
        max_length=200,
        help_text=_("Machine model or type designation"),
    )

    class Meta:
        verbose_name = _("Machine")
        verbose_name_plural = _("Machines")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of machine."""
        return f"{self.name} ({self.serial_number})"


class ComponentType(
    TimeStampedModel,
    BaseUserTracked,
    core_models.NameDescription,
    core_models.IsActive,
):
    """
    Component Type model.

    Represents categories/types of industrial components
    (e.g., Pump, Motor, Compressor, Turbine, etc.)
    """

    class Meta:
        verbose_name = _("Component Type")
        verbose_name_plural = _("Component Types")
        ordering = ("name",)


class Component(TimeStampedModel, BaseUserTracked, IsActive):
    """
    Component model.

    Represents parts or components installed in a machine.
    """

    machine = models.ForeignKey(
        Machine,
        verbose_name=_("Machine"),
        on_delete=models.CASCADE,
        related_name="components",
        help_text=_("Machine this component belongs to"),
    )
    type = models.ForeignKey(
        ComponentType,
        verbose_name=_("Type"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="components",
        help_text=_("Type/category of this component"),
    )

    class Meta:
        verbose_name = _("Component")
        verbose_name_plural = _("Components")
        ordering = ("machine", "type")
        indexes = [
            models.Index(fields=["machine", "is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of component."""
        type_name = self.type.name if self.type else "Unknown Type"
        return f"{type_name}({self.machine.name})"
