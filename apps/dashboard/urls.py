from django.urls import path

from apps.dashboard import views

app_name = "apps.dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
]
