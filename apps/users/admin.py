from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users import models
from apps.users.forms import CustomUserChangeForm, CustomUserCreationForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = models.User
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
        "is_active",
        "is_email_verified",
    )
    list_filter = (
        "is_active",
        "is_staff",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "avatar")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_superuser",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

    def is_email_verified(self, obj):
        email = EmailAddress.objects.filter(user=obj, primary=True).first()
        return email.verified if email else False

    is_email_verified.short_description = "Verified"
    is_email_verified.boolean = True

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)


admin.site.register(models.User, CustomUserAdmin)


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ["user"]
    exclude = ("is_removed",)
