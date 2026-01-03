from allauth.account.models import EmailAddress
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.users import models


class ToggleUserStatusView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        user = get_object_or_404(models.User, id=int(user_id))

        if action == "activate":
            user.is_active = True
        elif action == "deactivate":
            user.is_active = False
        else:
            return JsonResponse(
                {"success": False, "message": _("Invalid action")}
            )

        user.save()

        return JsonResponse(
            {
                "success": True,
                "message": _("User status has been successfully updated"),
                "is_active": user.is_active,
            }
        )


class UploadAvatarView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        avatar = request.FILES.get("avatar")

        if not avatar:
            return JsonResponse(
                {"success": False, "message": _("No file uploaded")}
            )

        user.avatar = avatar
        user.save()

        return JsonResponse(
            {
                "success": True,
                "message": _("Avatar has been successfully uploaded"),
                "avatar_url": user.avatar.url,
            }
        )


class VerifyEmailView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("user_id")

        if not user_id:
            return JsonResponse(
                {"success": False, "message": _("User ID is required")}
            )

        email_address = EmailAddress.objects.get(user_id=int(user_id))
        email_address.verified = True
        email_address.save()

        return JsonResponse(
            {
                "success": True,
                "message": _("Verification email has been successfully sent"),
            }
        )
