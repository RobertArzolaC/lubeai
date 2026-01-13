"""Service for bulk upload of inspection reports using polars."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import polars as pl
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

    Uses polars for high-performance Excel processing and bulk_create()
    for optimal batch performance. Handles entity resolution, data parsing,
    and creation of Report and LabAnalysis records.
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
        """
        Initialize service with user context and entity caches.

        Args:
            user: User performing the upload.
        """
        self.user = user
        # Entity resolution caches
        self._org_cache: Dict[str, Optional[users_models.Organization]] = {}
        self._machine_cache: Dict[
            Tuple, Optional[equipment_models.Machine]
        ] = {}
        self._component_cache: Dict[
            Tuple, Optional[equipment_models.Component]
        ] = {}

    def process_file(self, excel_file) -> Dict[str, Any]:
        """
        Process Excel file and create reports with lab analysis using polars.

        Args:
            excel_file: Uploaded Excel file (file-like object or path).

        Returns:
            Dict with processing results: created, updated, errors, skipped.
        """
        results = {"created": 0, "updated": 0, "errors": [], "skipped": 0}
        user_email = self.user.email

        logger.debug(
            f"Processing Excel file - User: {user_email}, "
            f"File: {getattr(excel_file, 'name', str(excel_file))}"
        )

        try:
            # Load Excel with polars
            df = pl.read_excel(excel_file)

            # Skip title row only (row 0), header filtering done later
            df = df.slice(1)

            # Select only the first 57 columns (0-56) to exclude blank columns
            if df.width > 57:
                df = df.select(df.columns[:57])
                logger.debug(
                    "Selected first 57 columns, excluded blank columns"
                )

            # Process DataFrame
            results = self.process_dataframe(df)

            logger.info(
                f"Finished processing Excel file - User: {user_email}, "
                f"File: {getattr(excel_file, 'name', str(excel_file))}, "
                f"Created: {results['created']}, "
                f"Skipped: {results['skipped']}, "
                f"Errors: {len(results['errors'])}"
            )

        except Exception as e:
            logger.exception(
                f"Fatal error processing file - User: {user_email}, "
                f"File: {getattr(excel_file, 'name', str(excel_file))}, "
                f"Error: {e}"
            )
            results["errors"].append(f"Fatal error: {str(e)}")

        return results

    def process_dataframe(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Process polars DataFrame directly (for ETL use).

        Args:
            df: Polars DataFrame with report data (already sliced to skip headers).

        Returns:
            Dict with processing results: created, updated, errors, skipped.
        """
        results = {"created": 0, "updated": 0, "errors": [], "skipped": 0}

        # Filter out empty rows
        df = df.filter(pl.any_horizontal(pl.all().is_not_null()))

        if len(df) == 0:
            logger.info(
                "DataFrame is empty after filtering, nothing to process"
            )
            return results

        # Rename columns to column_0, column_1, etc. for easier access
        df = df.rename({col: f"column_{i}" for i, col in enumerate(df.columns)})

        # Filter out title/header rows
        df = self._filter_header_rows(df)

        if len(df) == 0:
            logger.info("No data rows found after header filtering")
            return results

        # Extract lab numbers to check for duplicates
        lab_numbers = self._extract_lab_numbers(df)

        # Get existing lab numbers from database
        existing_lab_numbers = self._get_existing_lab_numbers(lab_numbers)
        results["skipped"] = len(existing_lab_numbers)

        # Filter out duplicates
        if existing_lab_numbers:
            df = df.filter(
                ~pl.col("column_1").is_in(list(existing_lab_numbers))
            )

        if len(df) == 0:
            logger.info("All records are duplicates, nothing to create")
            return results

        # Process all rows and collect data
        report_data_list = []
        lab_analysis_data_list = []

        for row_num, row in enumerate(df.iter_rows(named=True), start=3):
            try:
                report_data, lab_data = self._extract_row_data(row, row_num)

                # Validate required fields
                if not report_data.get("lab_number"):
                    results["errors"].append(
                        {
                            "row_number": row_num,
                            "lab_number": None,
                            "error": "Lab Number is required",
                            "field": "lab_number",
                        }
                    )
                    continue

                # Resolve entities with caching
                try:
                    organization = self._resolve_organization_cached(
                        report_data.get("organization_name")
                    )
                    machine = self._resolve_machine_cached(
                        report_data.get("machine_name"),
                        report_data.get("serial_number_code"),
                        organization,
                    )
                    component = self._resolve_component_cached(
                        report_data.get("component_name"), machine
                    )

                    report_data["organization"] = organization
                    report_data["machine"] = machine
                    report_data["component"] = component

                    report_data_list.append(report_data)
                    lab_analysis_data_list.append(lab_data)

                except ValidationError as e:
                    results["errors"].append(
                        {
                            "row_number": row_num,
                            "lab_number": report_data.get("lab_number"),
                            "error": str(e),
                            "field": "entity_resolution",
                        }
                    )

            except Exception as e:
                results["errors"].append(
                    {
                        "row_number": row_num,
                        "lab_number": None,
                        "error": str(e),
                        "field": "unknown",
                    }
                )
                logger.exception(
                    f"Unexpected error processing row {row_num}: {e}"
                )

        # Bulk create reports and lab analyses
        if report_data_list:
            try:
                with transaction.atomic():
                    created_reports = self._bulk_create_reports(
                        report_data_list
                    )
                    self._bulk_create_lab_analyses(
                        created_reports, lab_analysis_data_list
                    )
                    results["created"] = len(created_reports)

                logger.info(
                    f"Bulk created {len(created_reports)} reports with analyses"
                )

            except Exception as e:
                logger.exception(f"Error during bulk creation: {e}")
                results["errors"].append(
                    {
                        "row_number": None,
                        "lab_number": None,
                        "error": f"Bulk creation failed: {str(e)}",
                        "field": "bulk_create",
                    }
                )
                results["created"] = 0

        return results

    def _filter_header_rows(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Filter out title and header rows from DataFrame.

        Args:
            df: Input DataFrame.

        Returns:
            Filtered DataFrame without header rows.
        """
        # Title patterns to exclude
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

        # Filter rows where first column doesn't contain header patterns
        for pattern in title_patterns:
            df = df.filter(
                ~pl.col("column_0")
                .cast(pl.Utf8)
                .str.to_uppercase()
                .str.contains(pattern)
            )

        return df

    def _extract_lab_numbers(self, df: pl.DataFrame) -> List[str]:
        """
        Extract lab numbers from DataFrame.

        Args:
            df: Input DataFrame.

        Returns:
            List of lab numbers.
        """
        lab_numbers = (
            df.select("column_1")
            .to_series()
            .cast(pl.Utf8)
            .drop_nulls()
            .to_list()
        )
        return [ln for ln in lab_numbers if ln and str(ln).strip()]

    def _get_existing_lab_numbers(self, lab_numbers: List[str]) -> Set[str]:
        """
        Query existing lab numbers from database.

        Args:
            lab_numbers: List of lab numbers to check.

        Returns:
            Set of existing lab numbers.
        """
        if not lab_numbers:
            return set()

        existing = models.Report.objects.filter(
            lab_number__in=lab_numbers
        ).values_list("lab_number", flat=True)

        return set(existing)

    def _extract_row_data(
        self, row: Dict[str, Any], row_num: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract Report and LabAnalysis data from DataFrame row.

        Args:
            row: DataFrame row as dict.
            row_num: Row number for error reporting.

        Returns:
            Tuple of (report_data, lab_analysis_data).
        """
        indices = self.REPORT_COLUMN_INDICES

        # Extract machine name to determine transport type
        machine_name = self._safe_get_value(row, indices["machine_name"])
        is_transport = (
            "TRANSPORTES" in str(machine_name).upper()
            if machine_name
            else False
        )

        # Parse hours/kms based on vehicle type
        machine_hours_kms_value = self._safe_get_value(
            row, indices["machine_hours_kms"]
        )
        lubricant_hours_kms_value = self._safe_get_value(
            row, indices["lubricant_hours_kms"]
        )

        machine_hours, machine_kms = self._parse_hours_kms(
            machine_hours_kms_value, is_transport
        )
        lubricant_hours, lubricant_kms = self._parse_hours_kms(
            lubricant_hours_kms_value, is_transport
        )

        report_data = {
            "lab_number": self._safe_get_value(row, indices["lab_number"]),
            "organization_name": self._safe_get_value(
                row, indices["organization_name"]
            ),
            "machine_name": machine_name,
            "component_name": self._safe_get_value(
                row, indices["component_name"]
            ),
            "serial_number_code": self._safe_get_value(
                row, indices["serial_number_code"]
            ),
            "lubricant": self._safe_get_value(row, indices["lubricant"]) or "",
            "sample_date": self._parse_date(
                self._safe_get_value(row, indices["sample_date"])
            ),
            "machine_hours": machine_hours,
            "machine_kms": machine_kms,
            "lubricant_hours": lubricant_hours,
            "lubricant_kms": lubricant_kms,
            "reception_date": self._parse_date(
                self._safe_get_value(row, indices["reception_date"])
            ),
            "report_date": self._parse_date(
                self._safe_get_value(row, indices["report_date"])
            ),
            "filter_change": self._safe_get_value(row, indices["filter_change"])
            or "",
            "oil_change": self._safe_get_value(row, indices["oil_change"])
            or "",
            "per_number": self._safe_get_value(row, indices["per_number"])
            or "",
            "others": self._safe_get_value(row, indices["others"]) or "",
            "condition": self._parse_condition(
                self._safe_get_value(row, indices["condition"])
            ),
            "notes": self._safe_get_value(row, indices["notes"]) or "",
        }

        lab_analysis_data = self._extract_lab_analysis_data(row)

        return report_data, lab_analysis_data

    def _extract_lab_analysis_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract LabAnalysis data from DataFrame row.

        Args:
            row: DataFrame row as dict.

        Returns:
            Dictionary with lab analysis data.
        """
        indices = self.LAB_ANALYSIS_COLUMN_INDICES
        data = {}

        for field_name, col_index in indices.items():
            raw_value = self._safe_get_value(row, col_index)

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

    def _safe_get_value(self, row: Dict[str, Any], index: int) -> Any:
        """
        Safely get value from row dict by column index.

        Args:
            row: Row dictionary with column_N keys.
            index: Column index.

        Returns:
            Value or None.
        """
        col_name = f"column_{index}"
        return row.get(col_name)

    def _bulk_create_reports(
        self, report_data_list: List[Dict[str, Any]]
    ) -> List[models.Report]:
        """
        Bulk create Report records.

        Args:
            report_data_list: List of report data dictionaries.

        Returns:
            List of created Report instances.
        """
        reports_to_create = []

        for report_data in report_data_list:
            report = models.Report(
                lab_number=report_data["lab_number"],
                organization=report_data["organization"],
                machine=report_data["machine"],
                component=report_data["component"],
                lubricant=report_data["lubricant"],
                lubricant_hours=report_data["lubricant_hours"],
                lubricant_kms=report_data["lubricant_kms"],
                machine_hours=report_data["machine_hours"],
                machine_kms=report_data["machine_kms"],
                serial_number_code=report_data["serial_number_code"],
                sample_date=report_data["sample_date"],
                per_number=report_data["per_number"],
                reception_date=report_data["reception_date"],
                report_date=report_data["report_date"],
                filter_change=report_data["filter_change"],
                oil_change=report_data["oil_change"],
                others=report_data["others"],
                condition=report_data["condition"],
                notes=report_data["notes"],
                is_active=True,
                created_by=self.user,
                modified_by=self.user,
            )
            reports_to_create.append(report)

        created_reports = models.Report.objects.bulk_create(reports_to_create)

        return created_reports

    def _bulk_create_lab_analyses(
        self,
        reports: List[models.Report],
        lab_analysis_data_list: List[Dict[str, Any]],
    ) -> List[models.LabAnalysis]:
        """
        Bulk create LabAnalysis records.

        Args:
            reports: List of created Report instances.
            lab_analysis_data_list: List of lab analysis data dictionaries.

        Returns:
            List of created LabAnalysis instances.
        """
        analyses_to_create = []

        for report, lab_data in zip(reports, lab_analysis_data_list):
            analysis = models.LabAnalysis(
                report=report,
                created_by=self.user,
                modified_by=self.user,
                **lab_data,
            )
            analyses_to_create.append(analysis)

        created_analyses = models.LabAnalysis.objects.bulk_create(
            analyses_to_create
        )

        return created_analyses

    def _resolve_organization_cached(
        self, organization_name: str
    ) -> Optional[users_models.Organization]:
        """
        Resolve organization by name with caching.

        Args:
            organization_name: Organization name.

        Returns:
            Organization instance or None.

        Raises:
            ValidationError: If organization not found.
        """
        if not organization_name:
            return None

        if organization_name not in self._org_cache:
            try:
                self._org_cache[organization_name] = (
                    users_models.Organization.objects.get(
                        name__iexact=organization_name, is_active=True
                    )
                )
            except users_models.Organization.DoesNotExist:
                self._org_cache[organization_name] = None

        if self._org_cache[organization_name] is None:
            raise ValidationError(
                f"Organization '{organization_name}' not found"
            )

        return self._org_cache[organization_name]

    def _resolve_machine_cached(
        self,
        machine_name: str,
        serial_number: str,
        organization: users_models.Organization,
    ) -> Optional[equipment_models.Machine]:
        """
        Resolve machine by name and serial number with caching.

        Args:
            machine_name: Machine name.
            serial_number: Serial number.
            organization: Organization instance.

        Returns:
            Machine instance or None.

        Raises:
            ValidationError: If machine not found or multiple found.
        """
        if not machine_name:
            return None

        cache_key = (
            machine_name,
            serial_number,
            organization.id if organization else None,
        )

        if cache_key not in self._machine_cache:
            try:
                self._machine_cache[cache_key] = (
                    equipment_models.Machine.objects.get(
                        organization=organization,
                        name__iexact=machine_name,
                        serial_number__iexact=serial_number,
                        is_active=True,
                    )
                )
            except equipment_models.Machine.DoesNotExist:
                self._machine_cache[cache_key] = None
                logger.debug(
                    f"Machine lookup failed - Machine: {machine_name}, "
                    f"Serial Number: {serial_number}, Organization: {organization}"
                )
            except equipment_models.Machine.MultipleObjectsReturned:
                self._machine_cache[cache_key] = None
                logger.debug(
                    f"Multiple machines found - Machine: {machine_name}, "
                    f"Organization: {organization}"
                )

        if self._machine_cache[cache_key] is None:
            raise ValidationError(f"Machine '{machine_name}' not found")

        return self._machine_cache[cache_key]

    def _resolve_component_cached(
        self, component_name: str, machine: equipment_models.Machine
    ) -> Optional[equipment_models.Component]:
        """
        Resolve component by name and machine with caching.

        Args:
            component_name: Component name.
            machine: Machine instance.

        Returns:
            Component instance or None.

        Raises:
            ValidationError: If component not found.
        """
        if not component_name or not machine:
            return None

        # Clean component name
        component_name = component_name.replace("  ", " ").strip()

        cache_key = (component_name, machine.id if machine else None)

        if cache_key not in self._component_cache:
            try:
                self._component_cache[cache_key] = (
                    equipment_models.Component.objects.get(
                        machine=machine,
                        type__name__iexact=component_name,
                        is_active=True,
                    )
                )
            except equipment_models.Component.DoesNotExist:
                self._component_cache[cache_key] = None
                logger.debug(
                    f"Component lookup failed - Component: {component_name}, "
                    f"Machine: {machine}"
                )

        if self._component_cache[cache_key] is None:
            raise ValidationError(f"Component '{component_name}' not found")

        return self._component_cache[cache_key]

    def _parse_hours_kms(
        self, value: Any, is_transport: bool
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Parse hours/kms value based on transport type.

        Args:
            value: The raw value from the file.
            is_transport: True if vehicle contains "TRANSPORTES" (uses kms).

        Returns:
            Tuple of (hours, kms) where one will be the parsed value.
        """
        parsed_value = self._parse_integer(value)

        if is_transport:
            # Transport vehicles use kilometers
            return 0, parsed_value
        else:
            # Non-transport equipment uses hours
            return parsed_value, 0

    def _parse_integer(self, value: Any) -> Optional[int]:
        """
        Parse value to integer.

        Args:
            value: Raw value.

        Returns:
            Parsed integer or 0.
        """
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
        """
        Parse value to decimal.

        Args:
            value: Raw value.

        Returns:
            Parsed decimal or None.
        """
        if not value or value == "-":
            return None

        try:
            # Clean the value
            value_str = str(value).strip().replace(",", "")
            return float(value_str)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, date_value: Any) -> Optional[object]:
        """
        Parse date string to Django date object.

        Args:
            date_value: Date value to parse.

        Returns:
            Parsed date or None.
        """
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
        """
        Parse condition value to valid ReportCondition choice.

        Args:
            condition_value: Raw condition value.

        Returns:
            Validated condition choice.
        """
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
