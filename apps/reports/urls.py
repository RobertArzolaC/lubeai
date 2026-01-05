"""Reports URLs configuration."""

from django.urls import path

from apps.reports import views

app_name = "apps.reports"

urlpatterns = [
    # Report CRUD URLs
    path("reports/", views.ReportListView.as_view(), name="report_list"),
    path(
        "reports/create/",
        views.ReportCreateView.as_view(),
        name="report_create",
    ),
    path(
        "reports/<int:pk>/",
        views.ReportDetailView.as_view(),
        name="report_detail",
    ),
    path(
        "reports/<int:pk>/update/",
        views.ReportUpdateView.as_view(),
        name="report_update",
    ),
    path(
        "reports/<int:pk>/delete/",
        views.ReportDeleteView.as_view(),
        name="report_delete",
    ),
    # Bulk upload URLs
    path(
        "reports/bulk-upload/",
        views.ReportBulkUploadView.as_view(),
        name="report_bulk_upload",
    ),
    path(
        "reports/bulk-upload/template/",
        views.ReportBulkTemplateView.as_view(),
        name="report_bulk_template",
    ),
]
