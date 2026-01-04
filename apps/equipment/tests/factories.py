"""Equipment model factories for testing."""

import factory
from django.contrib.auth import get_user_model

from apps.equipment import models
from apps.users.tests import factories as user_factories

User = get_user_model()


class MachineFactory(factory.django.DjangoModelFactory):
    """Factory for Machine model."""

    class Meta:
        model = models.Machine

    organization = factory.SubFactory(user_factories.OrganizationFactory)
    name = factory.Faker("word")
    serial_number = factory.Sequence(lambda n: f"SN-{n:06d}")
    model = factory.Faker("word")
    is_active = True
    created_by = factory.SubFactory(user_factories.UserFactory)
    modified_by = factory.SelfAttribute("created_by")


class MachineTypeFactory(factory.django.DjangoModelFactory):
    """Factory for MachineType model."""

    class Meta:
        model = models.MachineType

    name = factory.Sequence(lambda n: f"Machine Type {n}")
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True
    created_by = factory.SubFactory(user_factories.UserFactory)
    modified_by = factory.SelfAttribute("created_by")


class ComponentFactory(factory.django.DjangoModelFactory):
    """Factory for Component model."""

    class Meta:
        model = models.Component

    machine = factory.SubFactory(MachineFactory)
    type = factory.SubFactory(MachineTypeFactory)
    serial_number = factory.Sequence(lambda n: f"COMP-{n:06d}")
    installation_datetime = factory.Faker("date_time_this_year", tzinfo=factory.Faker("pytimezone"))
    is_active = True
    created_by = factory.SubFactory(user_factories.UserFactory)
    modified_by = factory.SelfAttribute("created_by")
