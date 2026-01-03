from django import template
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag(takes_context=True)
def breadcrumb(context):
    request = context["request"]
    breadcrumbs = [
        {
            "title": _("Dashboard"),
            "url": "/dashboard/",
            "is_active": request.path == reverse("apps.dashboard:index"),
        }
    ]
    path_parts = request.path.split("/")
    current_path = f"/{path_parts[1]}/"

    for part in path_parts[2:]:
        if part:
            current_path += f"{part}/"
            try:
                url_name = resolve(current_path).url_name
                if "list" in url_name:
                    entity = url_name.split("_")[0]
                    title = f"{entity.title()}s"
                elif (
                    "detail" in url_name
                    or "update" in url_name
                    or "create" in url_name
                ):
                    action = url_name.split("_")[1]
                    title = action.title()
                else:
                    title = url_name.title()
                breadcrumbs.append(
                    {
                        "title": _(title),
                        "url": current_path,
                        "is_active": current_path == request.path,
                    }
                )
            except Resolver404:
                pass

    return breadcrumbs
