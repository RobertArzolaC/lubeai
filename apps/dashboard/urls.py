from django.urls import path

from apps.dashboard import views

app_name = "apps.dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    # Admin API endpoints
    path("api/data/", views.DashboardDataAPIView.as_view(), name="data_api"),
    path(
        "api/machines/",
        views.MachinesByOrganizationAPIView.as_view(),
        name="machines_api",
    ),
    # Organization Dashboard API endpoints
    path(
        "api/org/overview/",
        views.OrganizationDashboardOverviewAPIView.as_view(),
        name="org_overview_api",
    ),
    # Export endpoints
    path("export/", views.ExportPageView.as_view(), name="export"),
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
