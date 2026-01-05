from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class PermissionFormMixin:
    PERMISSION_MAPPING = {
        "account": {"app": "users", "model": "account"},
        "organization": {"app": "users", "model": "organization"},
        "machine": {"app": "equipment", "model": "machine"},
        "component": {"app": "equipment", "model": "component"},
        "report": {"app": "reports", "model": "report"},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permission_fields = self._create_permission_fields()

    def _create_permission_fields(self):
        actions = ["view", "add", "change", "delete"]
        permission_fields = {}

        for model_key, info in self.PERMISSION_MAPPING.items():
            for action in actions:
                field_name = f"can_{action}_{model_key}"
                codename = f"{action}_{info['model']}"
                permission_fields[field_name] = forms.BooleanField(
                    required=False,
                    label=_(f"Can {action} {model_key}"),
                    initial=self._get_initial_permission(
                        info["app"], info["model"], codename
                    ),
                )
                self.fields[field_name] = permission_fields[field_name]

        return permission_fields

    def _get_initial_permission(self, app_label, model_name, codename):
        if (
            hasattr(self, "instance")
            and self.instance
            and hasattr(self.instance, "user")
        ):
            return self.instance.user.has_perm(f"{app_label}.{codename}")
        return False

    def save_permissions(self, user):
        for field_name, _ in self.permission_fields.items():
            action = field_name.split("_")[1]
            model_key = field_name.split("_")[2]
            model_info = self.PERMISSION_MAPPING[model_key]

            try:
                content_type = ContentType.objects.get(
                    app_label=model_info["app"], model=model_info["model"]
                )
                permission = Permission.objects.get(
                    codename=f"{action}_{model_info['model']}",
                    content_type=content_type,
                )

                if self.cleaned_data.get(field_name):
                    user.user_permissions.add(permission)
                else:
                    user.user_permissions.remove(permission)
            except (Permission.DoesNotExist, ContentType.DoesNotExist):
                continue


class OrganizationRequiredMixin:
    """
    Mixin that ensures users have an organization associated.

    - Staff/superusers without organization can access (general dashboard)
    - Regular users without organization get 403 Forbidden
    - Users with organization see filtered content for their organization only
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Let the LoginRequiredMixin handle this
            return super().dispatch(request, *args, **kwargs)

        # Staff and superusers without organization can access general dashboard
        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Regular users must have an organization
        if not self.get_user_organization():
            raise PermissionDenied(
                _("Access denied. You must belong to an organization.")
            )

        return super().dispatch(request, *args, **kwargs)

    def get_user_organization(self):
        """Return the organization associated with the current user."""
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return None

        # Check if user has an account with organization
        if (
            hasattr(user, "account")
            and user.account
            and user.account.organization
        ):
            return user.account.organization

        return None

    def has_organization_access(self):
        """Check if user should see organization-filtered content."""
        return bool(self.get_user_organization())
