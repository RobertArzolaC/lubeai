from django.urls import path

from apps.equipment import views

app_name = "apps.equipment"

urlpatterns = [
    # Machine URLs
    path("machines/", views.MachineListView.as_view(), name="machine_list"),
    path(
        "machines/create/",
        views.MachineCreateView.as_view(),
        name="machine_create",
    ),
    path(
        "machines/bulk-upload/",
        views.MachineBulkUploadView.as_view(),
        name="machine_bulk_upload",
    ),
    path(
        "machines/bulk-upload/template/",
        views.MachineBulkTemplateView.as_view(),
        name="machine_bulk_template",
    ),
    path(
        "machines/<int:pk>/",
        views.MachineDetailView.as_view(),
        name="machine_detail",
    ),
    path(
        "machines/<int:pk>/update/",
        views.MachineUpdateView.as_view(),
        name="machine_update",
    ),
    path(
        "machines/<int:pk>/delete/",
        views.MachineDeleteView.as_view(),
        name="machine_delete",
    ),
]
