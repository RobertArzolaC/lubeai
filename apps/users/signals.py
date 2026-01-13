from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import Account


@receiver(post_save, sender=Account)
def add_component_analysis_permission(sender, instance, created, **kwargs):
    """
    Add component analysis permissions to user when account is created.

    This signal automatically grants the 'view_component_analysis' and
    'export_component_analysis' permissions to any user when their Account
    is created, allowing them to access component analysis features in the dashboard.
    """
    if created:
        try:
            # Get the ComponentAnalysis content type from dashboard app
            content_type = ContentType.objects.get(
                app_label="dashboard", model="componentanalysis"
            )

            # Define the required permissions
            permissions_codename = [
                "view_component_analysis",
                "export_component_analysis",
            ]

            # Get the component analysis permissions
            permissions = Permission.objects.filter(
                content_type=content_type, codename__in=permissions_codename
            )

            # Add permissions to user
            for permission in permissions:
                instance.user.user_permissions.add(permission)

        except (ContentType.DoesNotExist, Permission.DoesNotExist):
            # If permission doesn't exist yet (e.g., during migrations),
            # silently pass - permission will need to be added manually
            pass
