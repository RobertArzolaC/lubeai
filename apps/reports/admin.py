from django.contrib import admin
from django.utils.html import format_html

from apps.reports.models import LabAnalysis, Report


class LabAnalysisInline(admin.StackedInline):
    """Inline admin for LabAnalysis."""

    model = LabAnalysis
    extra = 0
    can_delete = False
    fieldsets = (
        (
            "Pruebas de Agua",
            {
                "fields": ("water_crackle", "water_distillation"),
                "classes": ("collapse",),
            },
        ),
        (
            "Viscosidad",
            {
                "fields": ("viscosity_40c", "viscosity_100c"),
                "classes": ("collapse",),
            },
        ),
        (
            "Números de Ácido/Base",
            {
                "fields": ("compatibility", "tbn", "tan"),
                "classes": ("collapse",),
            },
        ),
        (
            "Análisis FTIR",
            {
                "fields": (
                    "oxidation",
                    "soot",
                    "nitration",
                    "sulfation",
                    "glycol",
                    "fuel_dilution",
                    "water_ftir",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Análisis de Partículas",
            {
                "fields": ("pq_index", "particle_count_iso"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metales de Desgaste (ppm)",
            {
                "fields": (
                    "iron_fe",
                    "chromium_cr",
                    "lead_pb",
                    "copper_cu",
                    "tin_sn",
                    "aluminum_al",
                    "nickel_ni",
                    "silver_ag",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Contaminantes (ppm)",
            {
                "fields": (
                    "silicon_si",
                    "boron_b",
                    "sodium_na",
                    "magnesium_mg",
                    "potassium_k",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Aditivos (ppm)",
            {
                "fields": (
                    "molybdenum_mo",
                    "titanium_ti",
                    "vanadium_v",
                    "manganese_mn",
                    "phosphorus_p",
                    "zinc_zn",
                    "calcium_ca",
                    "barium_ba",
                    "cadmium_cd",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Visual",
            {
                "fields": ("visual_appearance",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadatos",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created", "modified", "created_by", "modified_by")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin configuration for Report model."""

    list_display = (
        "lab_number",
        "organization",
        "machine_info",
        "component_display",
        "lubricant",
        "sample_date",
        "reception_date",
        "status_badge",
        "condition_badge",
        "has_analysis",
        "is_active",
    )
    list_filter = (
        "status",
        "condition",
        "is_active",
        "organization",
        "component__type",
        "sample_date",
        "reception_date",
        "report_date",
    )
    search_fields = (
        "lab_number",
        "per_number",
        "serial_number_code",
        "lubricant",
        "organization__name",
        "machine__name",
        "machine__serial_number",
        "component__type__name",
        "notes",
    )
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "modified_by",
        "component_name_display",
    )
    date_hierarchy = "sample_date"
    ordering = ("-sample_date", "-created")
    raw_id_fields = ("organization", "machine", "component")

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    ("lab_number", "per_number"),
                    ("organization", "machine", "component"),
                    "component_name_display",
                    ("lubricant", "serial_number_code"),
                    "status",
                    "condition",
                    "is_active",
                )
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    ("sample_date", "reception_date"),
                    "report_date",
                )
            },
        ),
        (
            "Horas y Kilometraje",
            {
                "fields": (
                    ("lubricant_hours", "lubricant_kms"),
                    ("machine_hours", "machine_kms"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Recomendaciones",
            {
                "fields": (
                    ("filter_change", "oil_change"),
                    "others",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Notas",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadatos",
            {
                "fields": (
                    ("created", "modified"),
                    ("created_by", "modified_by"),
                ),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [LabAnalysisInline]

    def machine_info(self, obj):
        """Display machine information."""
        if obj.machine:
            return f"{obj.machine.name} ({obj.machine.serial_number})"
        return "N/A"

    machine_info.short_description = "Máquina"

    def component_display(self, obj):
        """Display component information."""
        return obj.component_name

    component_display.short_description = "Componente"

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            "pending": "#ffc107",
            "in_progress": "#17a2b8",
            "completed": "#28a745",
            "cancelled": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Estado"

    def condition_badge(self, obj):
        """Display condition as colored badge."""
        colors = {
            "normal": "#28a745",
            "caution": "#ffc107",
            "critical": "#dc3545",
        }
        color = colors.get(obj.condition, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_condition_display(),
        )

    condition_badge.short_description = "Condición"

    def has_analysis(self, obj):
        """Check if report has analysis data."""
        return hasattr(obj, "analysis") and obj.analysis is not None

    has_analysis.boolean = True
    has_analysis.short_description = "Análisis"

    def component_name_display(self, obj):
        """Display component name as readonly field."""
        return obj.component_name

    component_name_display.short_description = "Nombre del Componente"

    def get_queryset(self, request):
        """Optimize queries."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "organization", "machine", "component", "component__type"
            )
            .prefetch_related("analysis")
        )


@admin.register(LabAnalysis)
class LabAnalysisAdmin(admin.ModelAdmin):
    """Admin configuration for LabAnalysis model."""

    list_display = (
        "report_lab_number",
        "report_organization",
        "report_machine",
        "total_wear_metals_display",
        "total_contaminants_display",
        "water_content",
        "viscosity_summary",
        "created",
    )
    list_filter = (
        "report__organization",
        "report__status",
        "report__condition",
        "created",
    )
    search_fields = (
        "report__lab_number",
        "report__organization__name",
        "report__machine__name",
        "visual_appearance",
    )
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "modified_by",
        "total_wear_metals_display",
        "total_contaminants_display",
        "additive_depletion_display",
    )
    raw_id_fields = ("report",)

    fieldsets = (
        (
            "Reporte Asociado",
            {"fields": ("report",)},
        ),
        (
            "Pruebas de Agua",
            {
                "fields": ("water_crackle", "water_distillation"),
                "classes": ("collapse",),
            },
        ),
        (
            "Viscosidad",
            {
                "fields": ("viscosity_40c", "viscosity_100c"),
                "classes": ("collapse",),
            },
        ),
        (
            "Números de Ácido/Base",
            {
                "fields": ("compatibility", "tbn", "tan"),
                "classes": ("collapse",),
            },
        ),
        (
            "Análisis FTIR",
            {
                "fields": (
                    "oxidation",
                    "soot",
                    "nitration",
                    "sulfation",
                    "glycol",
                    "fuel_dilution",
                    "water_ftir",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Análisis de Partículas",
            {
                "fields": ("pq_index", "particle_count_iso"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metales de Desgaste (ppm)",
            {
                "fields": (
                    "iron_fe",
                    "chromium_cr",
                    "lead_pb",
                    "copper_cu",
                    "tin_sn",
                    "aluminum_al",
                    "nickel_ni",
                    "silver_ag",
                ),
                "description": "Metales que indican desgaste de componentes de la máquina",
            },
        ),
        (
            "Contaminantes (ppm)",
            {
                "fields": (
                    "silicon_si",
                    "boron_b",
                    "sodium_na",
                    "magnesium_mg",
                    "potassium_k",
                ),
                "description": "Elementos que indican contaminación externa",
            },
        ),
        (
            "Aditivos (ppm)",
            {
                "fields": (
                    "molybdenum_mo",
                    "titanium_ti",
                    "vanadium_v",
                    "manganese_mn",
                    "phosphorus_p",
                    "zinc_zn",
                    "calcium_ca",
                    "barium_ba",
                    "cadmium_cd",
                ),
                "description": "Aditivos del lubricante para protección y rendimiento",
            },
        ),
        (
            "Visual y Resumen",
            {
                "fields": (
                    "visual_appearance",
                    "total_wear_metals_display",
                    "total_contaminants_display",
                    "additive_depletion_display",
                ),
            },
        ),
        (
            "Metadatos",
            {
                "fields": (
                    ("created", "modified"),
                    ("created_by", "modified_by"),
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def report_lab_number(self, obj):
        """Get lab number from report."""
        return obj.report.lab_number

    report_lab_number.short_description = "No. Laboratorio"
    report_lab_number.admin_order_field = "report__lab_number"

    def report_organization(self, obj):
        """Get organization from report."""
        return (
            obj.report.organization.name if obj.report.organization else "N/A"
        )

    report_organization.short_description = "Organización"
    report_organization.admin_order_field = "report__organization__name"

    def report_machine(self, obj):
        """Get machine from report."""
        return obj.report.machine.name if obj.report.machine else "N/A"

    report_machine.short_description = "Máquina"
    report_machine.admin_order_field = "report__machine__name"

    def total_wear_metals_display(self, obj):
        """Display total wear metals."""
        total = obj.total_wear_metals
        if total > 100:
            color = "#dc3545"  # red
        elif total > 50:
            color = "#ffc107"  # yellow
        else:
            color = "#28a745"  # green
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ppm</span>',
            color,
            total,
        )

    total_wear_metals_display.short_description = "Total Metales Desgaste"

    def total_contaminants_display(self, obj):
        """Display total contaminants."""
        total = obj.total_contaminants
        if total > 50:
            color = "#dc3545"  # red
        elif total > 25:
            color = "#ffc107"  # yellow
        else:
            color = "#28a745"  # green
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ppm</span>',
            color,
            total,
        )

    total_contaminants_display.short_description = "Total Contaminantes"

    def additive_depletion_display(self, obj):
        """Display additive depletion percentage."""
        pct = obj.additive_depletion_pct
        if pct is None:
            return "N/A"
        if pct < 50:
            color = "#dc3545"  # red
        elif pct < 75:
            color = "#ffc107"  # yellow
        else:
            color = "#28a745"  # green
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            pct,
        )

    additive_depletion_display.short_description = "Aditivos Restantes"

    def water_content(self, obj):
        """Display water content summary."""
        if obj.water_distillation:
            return f"{obj.water_distillation}%"
        elif obj.water_crackle:
            return obj.water_crackle
        elif obj.water_ftir:
            return f"{obj.water_ftir}% (FTIR)"
        return "N/A"

    water_content.short_description = "Agua"

    def viscosity_summary(self, obj):
        """Display viscosity summary."""
        if obj.viscosity_40c and obj.viscosity_100c:
            return f"{obj.viscosity_40c}/{obj.viscosity_100c} cSt"
        elif obj.viscosity_40c:
            return f"{obj.viscosity_40c} cSt @40°C"
        elif obj.viscosity_100c:
            return f"{obj.viscosity_100c} cSt @100°C"
        return "N/A"

    viscosity_summary.short_description = "Viscosidad"

    def get_queryset(self, request):
        """Optimize queries."""
        return (
            super()
            .get_queryset(request)
            .select_related("report", "report__organization", "report__machine")
        )
