from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.mixins import CacheMixin

class DashboardView(CacheMixin, TemplateView):
    template_name = "dashboard/index.html"
    cache_timeout = 300

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        context.update(
            {
                "last_updated": today,
            }
        )

        return context
