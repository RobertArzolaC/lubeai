from django.urls import path

from apps.dashboard import views

app_name = "apps.dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    path("api/data/", views.DashboardDataAPIView.as_view(), name="data_api"),
    path("export/", views.ExportPageView.as_view(), name="export_page"),
    path(
        "export/preview/",
        views.ExportPreviewAPIView.as_view(),
        name="export_preview",
    ),
    path(
        "export/download/",
        views.DashboardExportView.as_view(),
        name="export_download",
    ),
]
