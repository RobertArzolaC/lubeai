from django.views.generic import TemplateView


class Error404View(TemplateView):
    template_name = "errors/404.html"


class Error500View(TemplateView):
    template_name = "errors/500.html"


class Error403View(TemplateView):
    template_name = "errors/403.html"
