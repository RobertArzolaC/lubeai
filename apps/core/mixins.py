from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.cache import cache_page

from apps.core import choices


class AjaxDeleteViewMixin(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        object_id = kwargs.get("pk")
        entity_name = self.model._meta.verbose_name
        try:
            current_object = self.model.objects.get(pk=object_id)
            current_object.delete()
            return JsonResponse(
                {
                    "status": "success",
                    "message": _(f"The {entity_name} was successfully deleted."),
                }
            )
        except self.model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": _(f"{entity_name} not found.")},
                status=404,
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    def handle_no_permission(self):
        return JsonResponse(
            {
                "status": "error",
                "message": _("You do not have permission to delete this account."),
            },
            status=403,
        )


class CacheMixin(LoginRequiredMixin):
    cache_timeout = 60  # Tiempo en segundos

    def get_cache_timeout(self):
        return self.cache_timeout

    def get_cache_key_prefix(self, request):
        """
        Genera un prefijo único basado en el usuario autenticado.
        """
        user_id = request.user.id if request.user.is_authenticated else "anonymous"
        return f"user_{user_id}"

    def dispatch(self, request, *args, **kwargs):
        """
        Aplica el caché al método `dispatch`.
        """
        # Crear una clave personalizada basada en el usuario
        cache_key_prefix = self.get_cache_key_prefix(request)

        # Decorar el método con `cache_page` dinámicamente
        view = cache_page(
            timeout=self.get_cache_timeout(),
            key_prefix=cache_key_prefix,
        )(super().dispatch)

        return view(request, *args, **kwargs)
