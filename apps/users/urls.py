from django.urls import path

from apps.users import api, views

app_name = "apps.users"

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    # Accounts URLs
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path(
        "accounts/create/",
        views.AccountCreateView.as_view(),
        name="account_create",
    ),
    path(
        "accounts/update/<int:pk>/",
        views.AccountUpdateView.as_view(),
        name="account_update",
    ),
    path(
        "accounts/<int:pk>/delete/",
        views.AccountDeleteView.as_view(),
        name="account_delete",
    ),
    # Organizations URLs
    path(
        "organizations/",
        views.OrganizationListView.as_view(),
        name="organization_list",
    ),
    path(
        "organizations/create/",
        views.OrganizationCreateView.as_view(),
        name="organization_create",
    ),
    path(
        "organizations/<int:pk>/",
        views.OrganizationDetailView.as_view(),
        name="organization_detail",
    ),
    path(
        "organizations/<int:pk>/update/",
        views.OrganizationUpdateView.as_view(),
        name="organization_update",
    ),
    path(
        "organizations/<int:pk>/delete/",
        views.OrganizationDeleteView.as_view(),
        name="organization_delete",
    ),
    # API URLs
    path(
        "api/toggle-user-status/",
        api.ToggleUserStatusView.as_view(),
        name="toggle_user_status_api",
    ),
    path(
        "api/upload-avatar/",
        api.UploadAvatarView.as_view(),
        name="upload_avatar_api",
    ),
    path(
        "api/verify-email/",
        api.VerifyEmailView.as_view(),
        name="verify_email_api",
    ),
]
