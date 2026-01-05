import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users import models

logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.User)
def create_user_account(sender, instance, created, **kwargs):
    if created:
        try:
            # Only create account automatically if one doesn't exist
            # This prevents conflicts with forms that create accounts manually
            if not hasattr(instance, "account"):
                # Check if we have any active organizations to assign
                default_org = models.Organization.objects.filter(
                    is_active=True
                ).first()
                if default_org:
                    models.Account.objects.create(
                        user=instance, organization=default_org
                    )
                    logger.info(
                        f"Cuenta creada automáticamente para el usuario: {instance.email} con organización: {default_org.name}"
                    )
                else:
                    logger.warning(
                        f"No se pudo crear cuenta automáticamente para {instance.email}: No hay organizaciones activas"
                    )
        except Exception as e:
            logger.error(
                f"Error al crear cuenta para el usuario {instance.email}: {str(e)}"
            )
