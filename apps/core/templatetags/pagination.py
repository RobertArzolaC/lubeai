from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    query = context["request"].GET.copy()
    for k, v in kwargs.items():
        if isinstance(v, list):
            query[k] = v[0] if v else ""
        else:
            query[k] = v
    return "?" + urlencode({k: str(v) for k, v in query.items()})
