import logging
from typing import Any, Dict

from apps.equipment.models import Component
from apps.reports.models import Report

logger = logging.getLogger(__name__)


class ComponentAnalysisService:
    """Service for handling component analysis data and calculations."""

    # Threshold constants (in ppm for metals, other units as specified)
    THRESHOLDS = {
        "wear_metals": {
            "iron_fe": {"warning": 75, "critical": 100, "unit": "ppm"},
            "copper_cu": {"warning": 20, "critical": 30, "unit": "ppm"},
            "aluminum_al": {"warning": 15, "critical": 25, "unit": "ppm"},
        },
        "contamination": {
            "silicon_si": {"warning": 15, "critical": 20, "unit": "ppm"},
            "sodium_na": {"warning": 30, "critical": 50, "unit": "ppm"},
            "potassium_k": {"warning": 10, "critical": 15, "unit": "ppm"},
        },
        "oil_health": {
            "silicon_si": {"warning": 15, "critical": 20, "unit": "ppm"},
            "sodium_na": {"warning": 30, "critical": 50, "unit": "ppm"},
            "potassium_k": {"warning": 10, "critical": 15, "unit": "ppm"},
            "viscosity_100c": {
                "warning_low": None,  # Will be calculated dynamically
                "warning_high": None,
                "unit": "cSt",
            },
        },
        "additives": {
            "zinc_zn": {"warning": 800, "critical": 600, "unit": "ppm"},
            "phosphorus_p": {"warning": 900, "critical": 700, "unit": "ppm"},
            "magnesium_mg": {"warning": 1800, "critical": 1500, "unit": "ppm"},
            "calcium_ca": {"warning": 2000, "critical": 1500, "unit": "ppm"},
        },
    }

    def __init__(self, component_id: int):
        """
        Initialize service with component context.

        Args:
            component_id: ID of the component to analyze
        """
        self.component_id = component_id
        self.component = None
        self.reports_qs = None
        self._load_component()

    def _load_component(self):
        """Load component and prepare reports queryset."""
        try:
            self.component = Component.objects.select_related(
                "machine", "type"
            ).get(id=self.component_id, is_active=True)

            # Base queryset: reports for this component with analysis data
            self.reports_qs = (
                Report.objects.filter(
                    component=self.component,
                    is_active=True,
                    sample_date__isnull=False,
                )
                .select_related("analysis")
                .order_by("sample_date")
            )

        except Component.DoesNotExist:
            logger.error(f"Component {self.component_id} not found or inactive")
            raise ValueError(f"Component {self.component_id} not found")

    def get_component_summary(self) -> Dict[str, Any]:
        """
        Get summary information about the component.

        Returns:
            Dictionary with component details and measurement unit
        """
        if not self.component:
            return {}

        latest_report = self.reports_qs.last()
        measurement_unit = self.detect_measurement_unit()

        return {
            "component_id": self.component.id,
            "component_type": (
                self.component.type.name if self.component.type else "N/A"
            ),
            "machine_name": self.component.machine.name,
            "machine_serial": self.component.machine.serial_number,
            "machine_model": self.component.machine.model,
            "total_reports": self.reports_qs.count(),
            "latest_sample_date": (
                latest_report.sample_date.strftime("%Y-%m-%d")
                if latest_report
                else None
            ),
            "measurement_unit": measurement_unit,
        }

    def detect_measurement_unit(self) -> str:
        """
        Detect if the machine uses hours or kilometers as measurement unit.

        Returns:
            "hours" or "kilometers" based on available data
        """
        last_report = self.reports_qs.last()

        is_transport = True if str(last_report.machine.name).upper() else False

        return "kilometers" if is_transport else "hours"

    def get_wear_trends(self) -> Dict[str, Any]:
        """
        Get wear metal trends data (Fe, Cu, Al).

        Returns:
            Dictionary with series data and thresholds
        """
        reports = self.reports_qs.filter(analysis__isnull=False)

        data_series = {
            "iron_fe": [],
            "copper_cu": [],
            "aluminum_al": [],
        }
        dates = []

        for report in reports:
            if hasattr(report, "analysis"):
                analysis = report.analysis
                dates.append(report.sample_date.strftime("%Y-%m-%d"))

                data_series["iron_fe"].append(
                    float(analysis.iron_fe)
                    if analysis.iron_fe is not None
                    else None
                )
                data_series["copper_cu"].append(
                    float(analysis.copper_cu)
                    if analysis.copper_cu is not None
                    else None
                )
                data_series["aluminum_al"].append(
                    float(analysis.aluminum_al)
                    if analysis.aluminum_al is not None
                    else None
                )

        return {
            "dates": dates,
            "series": [
                {
                    "name": "Hierro (Fe)",
                    "data": data_series["iron_fe"],
                    "color": "#F1416C",
                },
                {
                    "name": "Cobre (Cu)",
                    "data": data_series["copper_cu"],
                    "color": "#FFC700",
                },
                {
                    "name": "Aluminio (Al)",
                    "data": data_series["aluminum_al"],
                    "color": "#009EF7",
                },
            ],
            "thresholds": self.THRESHOLDS["wear_metals"],
        }

    def get_contamination_alerts(self) -> Dict[str, Any]:
        """
        Get contamination data (Si, Na, K).

        Returns:
            Dictionary with series data and thresholds
        """
        reports = self.reports_qs.filter(analysis__isnull=False)

        data_series = {
            "silicon_si": [],
            "sodium_na": [],
            "potassium_k": [],
        }
        dates = []

        for report in reports:
            if hasattr(report, "analysis"):
                analysis = report.analysis
                dates.append(report.sample_date.strftime("%Y-%m-%d"))

                data_series["silicon_si"].append(
                    float(analysis.silicon_si)
                    if analysis.silicon_si is not None
                    else None
                )
                data_series["sodium_na"].append(
                    float(analysis.sodium_na)
                    if analysis.sodium_na is not None
                    else None
                )
                data_series["potassium_k"].append(
                    float(analysis.potassium_k)
                    if analysis.potassium_k is not None
                    else None
                )

        return {
            "dates": dates,
            "series": [
                {
                    "name": "Silicio (Si) - Polvo",
                    "data": data_series["silicon_si"],
                    "color": "#181C32",
                },
                {
                    "name": "Sodio (Na) - Refrigerante",
                    "data": data_series["sodium_na"],
                    "color": "#009EF7",
                },
                {
                    "name": "Potasio (K)",
                    "data": data_series["potassium_k"],
                    "color": "#50CD89",
                },
            ],
            "thresholds": self.THRESHOLDS["contamination"],
        }

    def get_oil_health(self) -> Dict[str, Any]:
        """
        Get oil health indicators (Si, Na, K, viscosity) with lubricant usage.

        Returns:
            Dictionary with series data, thresholds, and lubricant usage data
        """
        reports = self.reports_qs.filter(analysis__isnull=False)
        measurement_unit = self.detect_measurement_unit()

        data_series = {
            "silicon_si": [],
            "sodium_na": [],
            "potassium_k": [],
            "viscosity_100c": [],
            "lubricant_usage": [],
        }
        dates = []

        for report in reports:
            if hasattr(report, "analysis"):
                analysis = report.analysis
                dates.append(report.sample_date.strftime("%Y-%m-%d"))

                # Line series data for metals and viscosity
                data_series["silicon_si"].append(
                    float(analysis.silicon_si)
                    if analysis.silicon_si is not None
                    else None
                )
                data_series["sodium_na"].append(
                    float(analysis.sodium_na)
                    if analysis.sodium_na is not None
                    else None
                )
                data_series["potassium_k"].append(
                    float(analysis.potassium_k)
                    if analysis.potassium_k is not None
                    else None
                )
                data_series["viscosity_100c"].append(
                    float(analysis.viscosity_100c)
                    if analysis.viscosity_100c is not None
                    else None
                )

                # Lubricant usage data for bar chart
                if measurement_unit == "hours":
                    lubricant_value = (
                        float(report.lubricant_hours)
                        if report.lubricant_hours is not None
                        else None
                    )
                else:  # kilometers
                    lubricant_value = (
                        float(report.lubricant_kms)
                        if report.lubricant_kms is not None
                        else None
                    )
                data_series["lubricant_usage"].append(lubricant_value)

        # Determine unit label for display
        unit_label = "Horas" if measurement_unit == "hours" else "Kilómetros"

        return {
            "dates": dates,
            "measurement_unit": measurement_unit,
            "unit_label": unit_label,
            "series": [
                {
                    "name": f"Lubricante ({unit_label})",
                    "data": data_series["lubricant_usage"],
                    "color": "#A1A5B7",
                    "type": "column",
                },
                {
                    "name": "Silicio (Si) - ppm",
                    "data": data_series["silicon_si"],
                    "color": "#181C32",
                    "type": "line",
                },
                {
                    "name": "Sodio (Na) - ppm",
                    "data": data_series["sodium_na"],
                    "color": "#009EF7",
                    "type": "line",
                },
                {
                    "name": "Potasio (K) - ppm",
                    "data": data_series["potassium_k"],
                    "color": "#50CD89",
                    "type": "line",
                },
                {
                    "name": "Viscosidad @ 100°C (cSt)",
                    "data": data_series["viscosity_100c"],
                    "color": "#FFC700",
                    "type": "line",
                },
            ],
            "thresholds": self.THRESHOLDS["oil_health"],
        }

    def get_additives_trend(self) -> Dict[str, Any]:
        """
        Get additive elements trend (Zn, P, Mg, Ca).

        Returns:
            Dictionary with series data and thresholds
        """
        reports = self.reports_qs.filter(analysis__isnull=False)

        data_series = {
            "zinc_zn": [],
            "phosphorus_p": [],
            "magnesium_mg": [],
            "calcium_ca": [],
        }
        dates = []

        for report in reports:
            if hasattr(report, "analysis"):
                analysis = report.analysis
                dates.append(report.sample_date.strftime("%Y-%m-%d"))

                data_series["zinc_zn"].append(
                    float(analysis.zinc_zn)
                    if analysis.zinc_zn is not None
                    else None
                )
                data_series["phosphorus_p"].append(
                    float(analysis.phosphorus_p)
                    if analysis.phosphorus_p is not None
                    else None
                )
                data_series["magnesium_mg"].append(
                    float(analysis.magnesium_mg)
                    if analysis.magnesium_mg is not None
                    else None
                )
                data_series["calcium_ca"].append(
                    float(analysis.calcium_ca)
                    if analysis.calcium_ca is not None
                    else None
                )

        return {
            "dates": dates,
            "series": [
                {
                    "name": "Zinc (Zn)",
                    "data": data_series["zinc_zn"],
                    "color": "#7239EA",
                },
                {
                    "name": "Fósforo (P)",
                    "data": data_series["phosphorus_p"],
                    "color": "#F1416C",
                },
                {
                    "name": "Magnesio (Mg)",
                    "data": data_series["magnesium_mg"],
                    "color": "#50CD89",
                },
                {
                    "name": "Calcio (Ca)",
                    "data": data_series["calcium_ca"],
                    "color": "#FFC700",
                },
            ],
            "thresholds": self.THRESHOLDS["additives"],
        }

    def get_all_analysis_data(self) -> Dict[str, Any]:
        """
        Get complete analysis data including summary and all charts.

        Returns:
            Dictionary with all component analysis data
        """
        try:
            return {
                "summary": self.get_component_summary(),
                "wear_trends": self.get_wear_trends(),
                "contamination": self.get_contamination_alerts(),
                "oil_health": self.get_oil_health(),
                "additives": self.get_additives_trend(),
            }
        except Exception:
            logger.exception(
                f"Error getting analysis data for component {self.component_id}"
            )
            raise
