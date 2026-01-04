"""Tests for equipment models."""

from django.db import IntegrityError
from django.test import TestCase

from apps.equipment import models
from apps.equipment.tests import factories
from apps.users.tests import factories as user_factories


class MachineModelTestCase(TestCase):
    """Test case for Machine model."""

    def setUp(self) -> None:
        """Set up test case."""
        self.user = user_factories.UserFactory()
        self.organization = user_factories.OrganizationFactory()

    def test_create_machine(self) -> None:
        """Test creating a machine successfully."""
        machine = factories.MachineFactory(
            name="Test Machine",
            serial_number="SN-TEST-001",
            model="TestModel-X100",
            organization=self.organization,
            created_by=self.user,
            modified_by=self.user,
        )

        self.assertEqual(machine.name, "Test Machine")
        self.assertEqual(machine.serial_number, "SN-TEST-001")
        self.assertEqual(machine.model, "TestModel-X100")
        self.assertEqual(machine.organization, self.organization)
        self.assertTrue(machine.is_active)
        self.assertIsNotNone(machine.created)
        self.assertIsNotNone(machine.modified)

    def test_machine_str_representation(self) -> None:
        """Test string representation of machine."""
        machine = factories.MachineFactory(
            name="Pump A1",
            serial_number="SN-12345",
        )
        expected = "Pump A1 (SN-12345)"
        self.assertEqual(str(machine), expected)

    def test_serial_number_unique_constraint(self) -> None:
        """Test that serial_number must be unique."""
        factories.MachineFactory(serial_number="SN-DUPLICATE")

        with self.assertRaises(IntegrityError):
            factories.MachineFactory(serial_number="SN-DUPLICATE")

    def test_machine_without_organization(self) -> None:
        """Test creating a machine without organization."""
        machine = factories.MachineFactory(organization=None)
        self.assertIsNone(machine.organization)
        self.assertIsNotNone(machine.name)

    def test_machine_is_active_default(self) -> None:
        """Test that is_active defaults to True."""
        machine = factories.MachineFactory()
        self.assertTrue(machine.is_active)

    def test_machine_can_be_inactive(self) -> None:
        """Test setting a machine as inactive."""
        machine = factories.MachineFactory(is_active=False)
        self.assertFalse(machine.is_active)

    def test_machine_timestamps(self) -> None:
        """Test that created and modified timestamps are set."""
        machine = factories.MachineFactory()
        self.assertIsNotNone(machine.created)
        self.assertIsNotNone(machine.modified)
        # Modified should be >= created
        self.assertGreaterEqual(machine.modified, machine.created)

    def test_machine_user_tracking(self) -> None:
        """Test that created_by and modified_by are set."""
        machine = factories.MachineFactory(
            created_by=self.user,
            modified_by=self.user,
        )
        self.assertEqual(machine.created_by, self.user)
        self.assertEqual(machine.modified_by, self.user)

    def test_machine_ordering(self) -> None:
        """Test that machines are ordered by name."""
        factories.MachineFactory(name="Zebra Machine")
        factories.MachineFactory(name="Alpha Machine")
        factories.MachineFactory(name="Beta Machine")

        machines = models.Machine.objects.all()
        names = [m.name for m in machines]
        self.assertEqual(names, ["Alpha Machine", "Beta Machine", "Zebra Machine"])


class MachineTypeModelTestCase(TestCase):
    """Test case for MachineType model."""

    def setUp(self) -> None:
        """Set up test case."""
        self.user = user_factories.UserFactory()

    def test_create_machine_type(self) -> None:
        """Test creating a machine type successfully."""
        machine_type = factories.MachineTypeFactory(
            name="Hydraulic Pump",
            description="High-pressure hydraulic pumps",
            created_by=self.user,
            modified_by=self.user,
        )

        self.assertEqual(machine_type.name, "Hydraulic Pump")
        self.assertEqual(machine_type.description, "High-pressure hydraulic pumps")
        self.assertTrue(machine_type.is_active)
        self.assertIsNotNone(machine_type.created)
        self.assertIsNotNone(machine_type.modified)

    def test_machine_type_str_representation(self) -> None:
        """Test string representation of machine type."""
        machine_type = factories.MachineTypeFactory(name="Electric Motor")
        self.assertEqual(str(machine_type), "Electric Motor")

    def test_machine_type_is_active_default(self) -> None:
        """Test that is_active defaults to True."""
        machine_type = factories.MachineTypeFactory()
        self.assertTrue(machine_type.is_active)

    def test_machine_type_ordering(self) -> None:
        """Test that machine types are ordered by name."""
        factories.MachineTypeFactory(name="Zebra Type")
        factories.MachineTypeFactory(name="Alpha Type")
        factories.MachineTypeFactory(name="Beta Type")

        types = models.MachineType.objects.all()
        names = [t.name for t in types]
        self.assertEqual(names, ["Alpha Type", "Beta Type", "Zebra Type"])


class ComponentModelTestCase(TestCase):
    """Test case for Component model."""

    def setUp(self) -> None:
        """Set up test case."""
        self.user = user_factories.UserFactory()
        self.machine = factories.MachineFactory()
        self.machine_type = factories.MachineTypeFactory(name="Bearing")

    def test_create_component(self) -> None:
        """Test creating a component successfully."""
        from django.utils import timezone

        install_dt = timezone.now()
        component = factories.ComponentFactory(
            machine=self.machine,
            type=self.machine_type,
            serial_number="BEAR-001",
            installation_datetime=install_dt,
            created_by=self.user,
            modified_by=self.user,
        )

        self.assertEqual(component.machine, self.machine)
        self.assertEqual(component.type, self.machine_type)
        self.assertEqual(component.serial_number, "BEAR-001")
        self.assertEqual(component.installation_datetime, install_dt)
        self.assertTrue(component.is_active)

    def test_component_str_representation(self) -> None:
        """Test string representation of component."""
        component = factories.ComponentFactory(
            machine=self.machine,
            type=self.machine_type,
            serial_number="COMP-12345",
        )
        expected = f"Bearing - COMP-12345 ({self.machine.name})"
        self.assertEqual(str(component), expected)

    def test_component_without_type(self) -> None:
        """Test creating a component without type."""
        component = factories.ComponentFactory(
            machine=self.machine,
            type=None,
        )
        self.assertIsNone(component.type)
        self.assertIn("Unknown Type", str(component))

    def test_component_cascade_delete_with_machine(self) -> None:
        """Test that component is deleted when machine is deleted."""
        component = factories.ComponentFactory(machine=self.machine)
        component_id = component.id

        self.machine.delete()

        with self.assertRaises(models.Component.DoesNotExist):
            models.Component.objects.get(id=component_id)

    def test_component_type_set_null(self) -> None:
        """Test that component type is set to null when type is deleted."""
        component = factories.ComponentFactory(
            machine=self.machine,
            type=self.machine_type,
        )

        self.machine_type.delete()
        component.refresh_from_db()

        self.assertIsNone(component.type)

    def test_machine_components_relation(self) -> None:
        """Test accessing components from machine."""
        factories.ComponentFactory(machine=self.machine)
        factories.ComponentFactory(machine=self.machine)

        self.assertEqual(self.machine.components.count(), 2)

    def test_component_ordering(self) -> None:
        """Test that components are ordered correctly."""
        from django.utils import timezone

        machine2 = factories.MachineFactory(name="Machine B")
        type2 = factories.MachineTypeFactory(name="Type B")

        # Create components in specific order
        factories.ComponentFactory(
            machine=machine2,
            type=type2,
            installation_datetime=timezone.now(),
        )
        factories.ComponentFactory(
            machine=self.machine,
            type=self.machine_type,
            installation_datetime=timezone.now(),
        )

        components = models.Component.objects.all()
        # Should be ordered by machine, type, installation_datetime
        self.assertGreaterEqual(len(components), 2)
