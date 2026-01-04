"""User model factories for testing."""

import factory
from django.contrib.auth import get_user_model
from django_extensions.db.fields import AutoSlugField

from apps.users import models

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for Organization model."""

    class Meta:
        model = models.Organization

    name = factory.Sequence(lambda n: f"Organization {n}")
    tax_id = factory.Sequence(lambda n: f"TAX-{n:08d}")
    is_active = True
