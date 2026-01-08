"""
Report Bulk Upload Service.

Business logic for processing Excel files and creating/updating reports
with their associated laboratory analyses.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import openpyxl
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_date

from apps.equipment import models as equipment_models
from apps.reports import choices, models
from apps.users import models as users_models

logger = logging.getLogger(__name__)


class ReportBulkUploadService:
    """
    Service for processing bulk upload of inspection reports.

    Handles Excel file processing, entity resolution, data parsing,
    and creation/update of Report and LabAnalysis records.
    """

    # Column indices for Report fields (from CSV structure)
    REPORT_COLUMN_INDICES = {
        "row_number": 0,  # N°
        "lab_number": 1,  # No. Lab
        "organization_name": 2,  # Cliente
        "machine_name": 3,  # Equipo
        "component_name": 4,  # Componente
        "serial_number_code": 5,  # Cód/Núm Serie
        "lubricant": 6,  # Lubricante
        "sample_date": 7,  # Fecha Muestra
        "machine_hours_kms": 8,  # Equipo Horas/Kms
        "lubricant_hours_kms": 9,  # Lubricante Horas/Kms
        "reception_date": 10,  # Fecha de Recepción
        "report_date": 11,  # Fecha de Reporte
        "filter_change": 12,  # Cambio de Filtro
        "oil_change": 13,  # Cambio de Aceite
        "per_number": 14,  # No.Per
        "others": 15,  # Otros
        "condition": 16,  # Condición
        "notes": 17,  # Comentario
    }

    # Column indices for LabAnalysis fields
    LAB_ANALYSIS_COLUMN_INDICES = {
        "water_crackle": 18,  # ITS 009/18 - Agua (Crackle test)
        "water_distillation": 19,  # ASTM D 95-13 - Agua por destilación
        "viscosity_40c": 20,  # ASTM D 7279-20 - Viscosidad a 40°C
        "viscosity_100c": 21,  # ASTM D 7279-20 - Viscosidad a 100°C
        "compatibility": 22,  # ILT-096 - COMPATIBILIDAD
        "tbn": 23,  # ASTM D 2896-21 - Número Básico (TBN)
        "tan": 24,  # ASTM D 664-24 - Número Acido (TAN)
        "oxidation": 25,  # ASTM E 2412-23 - Oxidación
        "soot": 26,  # ASTM E 2412-23 - Hollín
        "nitration": 27,  # ASTM E 2412-23 - Nitración
        "sulfation": 28,  # ASTM E 2412-23 - Sulfatación
        "glycol": 29,  # ASTM E 2412-23 - Glicol
        "fuel_dilution": 30,  # ASTM E 2412-23 - Dilución
        "water_ftir": 31,  # ASTM E 2412-23 - Agua FTIR
        "pq_index": 32,  # ITS 044/15 - PQ Index
        "particle_count_iso": 33,  # ISO 4406:2021 - Conteo de Partículas
        "iron_fe": 34,  # ASTM D 5185-18 - Hierro (Fe)
        "chromium_cr": 35,  # ASTM D 5185-18 - Cromo (Cr)
        "lead_pb": 36,  # ASTM D 5185-18 - Plomo (Pb)
        "copper_cu": 37,  # ASTM D 5185-18 - Cobre (Cu)
        "tin_sn": 38,  # ASTM D 5185-18 - Estaño (Sn)
        "aluminum_al": 39,  # ASTM D 5185-18 - Aluminio (Al)
        "nickel_ni": 40,  # ASTM D 5185-18 - Níquel (Ni)
        "silver_ag": 41,  # ASTM D 5185-18 - Plata (Ag)
        "silicon_si": 42,  # ASTM D 5185-18 - Silicio (Si)
        "boron_b": 43,  # ASTM D 5185-18 - Boro (B)
        "sodium_na": 44,  # ASTM D 5185-18 - Sodio (Na)
        "magnesium_mg": 45,  # ASTM D 5185-18 - Magnesio (Mg)
        "molybdenum_mo": 46,  # ASTM D 5185-18 - Molibdeno (Mo)
        "titanium_ti": 47,  # ASTM D 5185-18 - Titanio (Ti)
        "vanadium_v": 48,  # ASTM D 5185-18 - Vanadio (V)
        "manganese_mn": 49,  # ASTM D 5185-18 - Manganeso (Mn)
        "potassium_k": 50,  # ASTM D 5185-18 - Potasio (K)
        "phosphorus_p": 51,  # ASTM D 5185-18 - Fósforo (P)
        "zinc_zn": 52,  # ASTM D 5185-18 - Zinc (Zn)
        "calcium_ca": 53,  # ASTM D 5185-18 - Calcio (Ca)
        "barium_ba": 54,  # ASTM D 5185-18 - Bario (Ba)
        "cadmium_cd": 55,  # ASTM D 5185-18 - Cadmio (Cd)
        "visual_appearance": 56,  # Apariencia - Visual
    }

    def __init__(self, user):
        """Initialize service with user context."""
        self.user = user

    def process_file(self, excel_file) -> Dict[str, Any]:
        """
        Process Excel file and create/update reports with lab analysis.

        Args:
            excel_file: Uploaded Excel file

        Returns:
            Dict with processing results: created, updated, errors, skipped
        """
        results = {"created": 0, "updated": 0, "errors": [], "skipped": 0}
        user_email = self.user.email

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
                    error_msg = f"Row {row_num}: {e.message if hasattr(e, 'message') else str(e)}"
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

    def _is_title_or_header_row(self, row: Tuple) -> bool:
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
            "N°",
        ]

        return any(pattern in first_cell for pattern in title_patterns)

    def _process_row(self, row: Tuple, row_num: int) -> str:
        """Process a single row from Excel."""
        # Extract Report data
        report_data = self._extract_report_data(row, row_num)

        # Validate required fields
        if not report_data.get("lab_number"):
            raise ValidationError("Lab Number is required")

        # Resolve related entities
        organization = self._resolve_organization(
            report_data.get("organization_name")
        )
        machine = self._resolve_machine(
            report_data.get("machine_name"),
            report_data.get("serial_number_code"),
            organization,
        )
        component = self._resolve_component(
            report_data.get("component_name"), machine
        )

        # Create or update report
        report, created = self._create_or_update_report(
            report_data, organization, machine, component
        )

        # Create or update lab analysis
        lab_analysis_data = self._extract_lab_analysis_data(row)
        self._create_or_update_lab_analysis(report, lab_analysis_data)

        return "created" if created else "updated"

    def _extract_report_data(self, row: Tuple, row_num: int) -> Dict[str, Any]:
        """Extract Report data from row."""
        indices = self.REPORT_COLUMN_INDICES

        # Get raw values
        machine_name = self._safe_get_cell(row, indices["machine_name"])
        machine_hours_kms_value = self._safe_get_cell(
            row, indices["machine_hours_kms"]
        )
        lubricant_hours_kms_value = self._safe_get_cell(
            row, indices["lubricant_hours_kms"]
        )

        # Determine if transport vehicle (uses kilometers) or not (uses hours)
        is_transport = (
            "TRANSPORTES" in str(machine_name).upper()
            if machine_name
            else False
        )

        # Parse hours/kms based on vehicle type
        machine_hours, machine_kms = self._parse_hours_kms(
            machine_hours_kms_value, is_transport
        )
        lubricant_hours, lubricant_kms = self._parse_hours_kms(
            lubricant_hours_kms_value, is_transport
        )

        return {
            "lab_number": self._safe_get_cell(row, indices["lab_number"]),
            "organization_name": self._safe_get_cell(
                row, indices["organization_name"]
            ),
            "machine_name": machine_name,
            "component_name": self._safe_get_cell(
                row, indices["component_name"]
            ),
            "serial_number_code": self._safe_get_cell(
                row, indices["serial_number_code"]
            ),
            "lubricant": self._safe_get_cell(row, indices["lubricant"]) or "",
            "sample_date": self._parse_date(
                self._safe_get_cell(row, indices["sample_date"])
            ),
            "machine_hours": machine_hours,
            "machine_kms": machine_kms,
            "lubricant_hours": lubricant_hours,
            "lubricant_kms": lubricant_kms,
            "reception_date": self._parse_date(
                self._safe_get_cell(row, indices["reception_date"])
            ),
            "report_date": self._parse_date(
                self._safe_get_cell(row, indices["report_date"])
            ),
            "filter_change": self._safe_get_cell(row, indices["filter_change"])
            or "",
            "oil_change": self._safe_get_cell(row, indices["oil_change"]) or "",
            "per_number": self._safe_get_cell(row, indices["per_number"]) or "",
            "others": self._safe_get_cell(row, indices["others"]) or "",
            "condition": self._parse_condition(
                self._safe_get_cell(row, indices["condition"])
            ),
            "notes": self._safe_get_cell(row, indices["notes"]) or "",
        }

    def _extract_lab_analysis_data(self, row: Tuple) -> Dict[str, Any]:
        """Extract LabAnalysis data from row."""
        indices = self.LAB_ANALYSIS_COLUMN_INDICES

        data = {}
        for field_name, col_index in indices.items():
            raw_value = self._safe_get_cell(row, col_index)

            # Parse based on field type
            if field_name in [
                "water_crackle",
                "compatibility",
                "particle_count_iso",
                "visual_appearance",
            ]:
                # String fields
                data[field_name] = str(raw_value) if raw_value else ""
            elif field_name in [
                "water_distillation",
                "viscosity_40c",
                "viscosity_100c",
                "tbn",
                "tan",
                "oxidation",
                "soot",
                "nitration",
                "sulfation",
                "glycol",
                "fuel_dilution",
                "water_ftir",
            ]:
                # Decimal fields
                data[field_name] = self._parse_decimal(raw_value)
            else:
                # Integer fields (metals, particles, etc.)
                data[field_name] = self._parse_integer(raw_value)

        return data

    def _safe_get_cell(self, row: Tuple, index: int) -> Any:
        """Safely get cell value from row by index."""
        try:
            return row[index] if index < len(row) else None
        except (IndexError, TypeError):
            return None

    def _parse_hours_kms(
        self, value: Any, is_transport: bool
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Parse hours/kms value based on transport type.

        Args:
            value: The raw value from the CSV
            is_transport: True if vehicle contains "TRANSPORTES" (uses kms), False for hours

        Returns:
            Tuple of (hours, kms) where one will be the parsed value and other will be 0
        """
        parsed_value = self._parse_integer(value)

        if is_transport:
            # Transport vehicles use kilometers
            return 0, parsed_value
        else:
            # Non-transport equipment uses hours
            return parsed_value, 0

    def _parse_integer(self, value: Any) -> Optional[int]:
        """Parse value to integer."""
        if not value or value == "-":
            return 0

        try:
            # Clean the value from any text and thousands separators
            value_str = str(value).strip().lower()
            # Remove text like 'horas', 'km' and commas
            value_str = (
                value_str.replace("horas", "")
                .replace("km", "")
                .replace(",", "")
                .strip()
            )

            # Convert to integer
            return int(float(value_str))
        except (ValueError, TypeError):
            return 0

    def _parse_decimal(self, value: Any) -> Optional[float]:
        """Parse value to decimal."""
        if not value or value == "-":
            return None

        try:
            # Clean the value
            value_str = str(value).strip().replace(",", "")
            return float(value_str)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, date_value: Any) -> Optional[object]:
        """Parse date string to Django date object."""
        if not date_value:
            return None

        # Convert to string if it's not already
        date_str = str(date_value).strip()

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

    def _parse_condition(self, condition_value: Any) -> str:
        """Parse condition value to valid ReportCondition choice."""
        if not condition_value:
            return choices.ReportCondition.NORMAL

        condition_str = str(condition_value).strip().lower()

        # Map common condition values
        condition_mapping = {
            "normal": choices.ReportCondition.NORMAL,
            "caution": choices.ReportCondition.CAUTION,
            "precaution": choices.ReportCondition.CAUTION,
            "precaucion": choices.ReportCondition.CAUTION,
            "critical": choices.ReportCondition.CRITICAL,
            "critico": choices.ReportCondition.CRITICAL,
            "alerta": choices.ReportCondition.CRITICAL,
        }

        return condition_mapping.get(
            condition_str, choices.ReportCondition.NORMAL
        )

    def _resolve_organization(
        self, organization_name: str
    ) -> Optional[users_models.Organization]:
        """Resolve organization by name."""
        if not organization_name:
            return None

        try:
            return users_models.Organization.objects.get(
                name__iexact=organization_name, is_active=True
            )
        except users_models.Organization.DoesNotExist:
            raise ValidationError(
                f"Organization '{organization_name}' not found"
            )

    def _resolve_machine(
        self,
        machine_name: str,
        serial_number: str,
        organization: users_models.Organization,
    ) -> Optional[equipment_models.Machine]:
        """Resolve machine by name and serial number."""
        if not machine_name:
            return None

        try:
            return equipment_models.Machine.objects.get(
                organization=organization,
                name__iexact=machine_name,
                serial_number__iexact=serial_number,
                is_active=True,
            )
        except equipment_models.Machine.DoesNotExist:
            logger.debug(
                f"Machine lookup failed - Machine: {machine_name}, "
                f"Serial Number: {serial_number}, Organization: {organization}"
            )
            raise ValidationError(f"Machine '{machine_name}' not found")
        except equipment_models.Machine.MultipleObjectsReturned:
            logger.debug(
                f"Multiple machines found - Machine: {machine_name}, Organization: {organization}"
            )
            raise ValidationError(
                f"Multiple machines found with name '{machine_name}'"
            )

    def _resolve_component(
        self, component_name: str, machine: equipment_models.Machine
    ) -> Optional[equipment_models.Component]:
        """Resolve component by name and machine."""
        if not component_name or not machine:
            return None

        try:
            # Clean component name
            component_name = component_name.replace("  ", " ").strip()
            return equipment_models.Component.objects.get(
                machine=machine,
                type__name__iexact=component_name,
                is_active=True,
            )
        except equipment_models.Component.DoesNotExist:
            logger.debug(
                f"Component lookup failed - Component: {component_name}, Machine: {machine}"
            )
            raise ValidationError(f"Component '{component_name}' not found")

    def _create_or_update_report(
        self, report_data: Dict[str, Any], organization, machine, component
    ) -> Tuple[models.Report, bool]:
        """Create or update report."""
        report, created = models.Report.objects.update_or_create(
            lab_number=report_data["lab_number"],
            defaults={
                "organization": organization,
                "machine": machine,
                "component": component,
                "lubricant": report_data["lubricant"],
                "lubricant_hours": report_data["lubricant_hours"],
                "lubricant_kms": report_data["lubricant_kms"],
                "machine_hours": report_data["machine_hours"],
                "machine_kms": report_data["machine_kms"],
                "serial_number_code": report_data["serial_number_code"],
                "sample_date": report_data["sample_date"],
                "per_number": report_data["per_number"],
                "reception_date": report_data["reception_date"],
                "report_date": report_data["report_date"],
                "filter_change": report_data["filter_change"],
                "oil_change": report_data["oil_change"],
                "others": report_data["others"],
                "condition": report_data["condition"],
                "notes": report_data["notes"],
                "is_active": True,
                "created_by": self.user,
                "modified_by": self.user,
            },
        )
        return report, created

    def _create_or_update_lab_analysis(
        self, report: models.Report, lab_data: Dict[str, Any]
    ) -> models.LabAnalysis:
        """Create or update laboratory analysis."""
        lab_analysis, created = models.LabAnalysis.objects.update_or_create(
            report=report,
            defaults={
                **lab_data,
                "created_by": self.user,
                "modified_by": self.user,
            },
        )
        return lab_analysis
