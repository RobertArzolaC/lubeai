"""
Test factories for reports app models.

Provides factory classes for creating test instances of Report and LabAnalysis models.
"""

import factory
from django.utils import timezone

from apps.equipment.tests import factories as equipment_factories
from apps.reports import choices, models
from apps.users.tests import factories as user_factories


class ReportFactory(factory.django.DjangoModelFactory):
    """Factory for creating Report test instances."""

    class Meta:
        model = models.Report

    organization = factory.SubFactory(user_factories.OrganizationFactory)
    machine = factory.SubFactory(
        equipment_factories.MachineFactory,
        organization=factory.SelfAttribute("..organization"),
    )
    component = factory.SubFactory(
        equipment_factories.ComponentFactory,
        machine=factory.SelfAttribute("..machine"),
    )
    lab_number = factory.Sequence(lambda n: f"LAB-{n:06d}")
    lubricant = factory.Faker("word")
    lubricant_hours = factory.Faker("random_int", min=0, max=5000)
    lubricant_kms = factory.Faker("random_int", min=0, max=50000)
    machine_hours = factory.Faker("random_int", min=0, max=10000)
    machine_kms = factory.Faker("random_int", min=0, max=100000)
    serial_number_code = factory.Sequence(lambda n: f"SN-{n:08d}")
    sample_date = factory.Faker(
        "date_between", start_date="-1y", end_date="today"
    )
    per_number = factory.Sequence(lambda n: f"PER-{n:05d}")
    reception_date = factory.LazyAttribute(
        lambda obj: obj.sample_date + timezone.timedelta(days=1)
        if obj.sample_date
        else None
    )
    status = factory.Iterator(
        [choice[0] for choice in choices.ReportStatus.choices]
    )
    condition = factory.Iterator(
        [choice[0] for choice in choices.ReportCondition.choices]
    )
    notes = factory.Faker("text", max_nb_chars=200)
    report_date = factory.LazyAttribute(
        lambda obj: obj.reception_date + timezone.timedelta(days=2)
        if obj.reception_date
        else None
    )
    filter_change = factory.Faker("random_element", elements=["YES", "NO", ""])
    oil_change = factory.Faker("random_element", elements=["YES", "NO", ""])
    others = factory.Faker("text", max_nb_chars=100)
    is_active = True
    created_by = factory.SubFactory(user_factories.UserFactory)
    modified_by = factory.SelfAttribute("created_by")


class LabAnalysisFactory(factory.django.DjangoModelFactory):
    """Factory for creating LabAnalysis test instances with realistic values."""

    class Meta:
        model = models.LabAnalysis

    report = factory.SubFactory(ReportFactory)
    created_by = factory.SelfAttribute("report.created_by")
    modified_by = factory.SelfAttribute("report.modified_by")

    # Water Tests
    water_crackle = factory.Faker(
        "random_element", elements=["NEGATIVO", "POSITIVO", ""]
    )
    water_distillation = factory.Faker(
        "pydecimal", left_digits=2, right_digits=3, positive=True, max_value=5
    )

    # Viscosity (cSt)
    viscosity_40c = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=20,
        max_value=500,
    )
    viscosity_100c = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=5,
        max_value=50,
    )

    # Acid/Base Numbers (mgKOH/g)
    compatibility = factory.Faker(
        "random_element", elements=["COMPATIBLE", "INCOMPATIBLE", ""]
    )
    tbn = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=1,
        max_value=15,
    )
    tan = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=0.5,
        max_value=5,
    )

    # FTIR Analysis
    oxidation = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=3,
        positive=True,
        max_value=50,
    )
    soot = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=3,
        positive=True,
        max_value=5,
    )
    nitration = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=3,
        positive=True,
        max_value=30,
    )
    sulfation = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=3,
        positive=True,
        max_value=30,
    )
    glycol = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=3,
        positive=True,
        max_value=5,
    )
    fuel_dilution = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=3,
        positive=True,
        max_value=10,
    )
    water_ftir = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=3,
        positive=True,
        max_value=5,
    )

    # Particle Analysis
    pq_index = factory.Faker("random_int", min=0, max=200)
    particle_count_iso = factory.Faker(
        "random_element", elements=["20/18/15", "19/17/14", "21/19/16", ""]
    )

    # Wear Metals (ppm)
    iron_fe = factory.Faker("random_int", min=0, max=200)
    chromium_cr = factory.Faker("random_int", min=0, max=50)
    lead_pb = factory.Faker("random_int", min=0, max=100)
    copper_cu = factory.Faker("random_int", min=0, max=150)
    tin_sn = factory.Faker("random_int", min=0, max=50)
    aluminum_al = factory.Faker("random_int", min=0, max=80)
    nickel_ni = factory.Faker("random_int", min=0, max=30)
    silver_ag = factory.Faker("random_int", min=0, max=20)

    # Contaminants (ppm)
    silicon_si = factory.Faker("random_int", min=0, max=150)
    boron_b = factory.Faker("random_int", min=0, max=50)
    sodium_na = factory.Faker("random_int", min=0, max=250)
    magnesium_mg = factory.Faker("random_int", min=0, max=100)
    potassium_k = factory.Faker("random_int", min=0, max=50)

    # Additives (ppm)
    molybdenum_mo = factory.Faker("random_int", min=0, max=200)
    titanium_ti = factory.Faker("random_int", min=0, max=20)
    vanadium_v = factory.Faker("random_int", min=0, max=20)
    manganese_mn = factory.Faker("random_int", min=0, max=20)
    phosphorus_p = factory.Faker("random_int", min=0, max=1500)
    zinc_zn = factory.Faker("random_int", min=0, max=1500)
    calcium_ca = factory.Faker("random_int", min=0, max=3000)
    barium_ba = factory.Faker("random_int", min=0, max=50)
    cadmium_cd = factory.Faker("random_int", min=0, max=10)

    # Visual
    visual_appearance = factory.Faker(
        "random_element",
        elements=[
            "Clear",
            "Slightly cloudy",
            "Dark",
            "Contaminated",
            "Normal",
            "",
        ],
    )


class NormalConditionLabAnalysisFactory(LabAnalysisFactory):
    """Factory for creating LabAnalysis with normal condition values."""

    # Wear metals - normal range
    iron_fe = factory.Faker("random_int", min=0, max=40)
    copper_cu = factory.Faker("random_int", min=0, max=25)
    aluminum_al = factory.Faker("random_int", min=0, max=15)

    # Contaminants - normal range
    silicon_si = factory.Faker("random_int", min=0, max=25)
    sodium_na = factory.Faker("random_int", min=0, max=40)
    fuel_dilution = factory.Faker(
        "pydecimal", left_digits=1, right_digits=2, positive=True, max_value=2.5
    )

    # Oil health - good condition
    tbn = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=5,
        max_value=12,
    )
    tan = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        max_value=2,
    )
    oxidation = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        max_value=15,
    )


class CautionConditionLabAnalysisFactory(LabAnalysisFactory):
    """Factory for creating LabAnalysis with caution condition values."""

    # Wear metals - caution range
    iron_fe = factory.Faker("random_int", min=50, max=100)
    copper_cu = factory.Faker("random_int", min=30, max=50)
    aluminum_al = factory.Faker("random_int", min=20, max=40)

    # Contaminants - caution range
    silicon_si = factory.Faker("random_int", min=30, max=50)
    sodium_na = factory.Faker("random_int", min=50, max=100)
    fuel_dilution = factory.Faker(
        "pydecimal", left_digits=1, right_digits=2, positive=True, min_value=3, max_value=5
    )

    # Oil health - degraded condition
    tbn = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        min_value=2,
        max_value=5,
    )
    tan = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        min_value=2,
        max_value=4,
    )
    oxidation = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=20,
        max_value=30,
    )


class CriticalConditionLabAnalysisFactory(LabAnalysisFactory):
    """Factory for creating LabAnalysis with critical condition values."""

    # Wear metals - critical range
    iron_fe = factory.Faker("random_int", min=100, max=200)
    copper_cu = factory.Faker("random_int", min=50, max=150)
    aluminum_al = factory.Faker("random_int", min=40, max=80)

    # Contaminants - critical range
    silicon_si = factory.Faker("random_int", min=50, max=150)
    sodium_na = factory.Faker("random_int", min=100, max=250)
    fuel_dilution = factory.Faker(
        "pydecimal", left_digits=1, right_digits=2, positive=True, min_value=5, max_value=10
    )

    # Oil health - severely degraded condition
    tbn = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        max_value=2,
    )
    tan = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        positive=True,
        min_value=4,
        max_value=8,
    )
    oxidation = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=30,
        max_value=50,
    )
