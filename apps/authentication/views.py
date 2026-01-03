from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.authentication import forms


@method_decorator(csrf_exempt, name="dispatch")
class ChangePasswordView(View):
    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, request.POST)
        response = {"status": "error", "errors": {}}

        if not form.is_valid():
            return JsonResponse(response, status=400)

        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse(
            {"status": "success", "message": "Password changed successfully."}
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeactivateAccountView(View):
    def post(self, request, *args, **kwargs):
        form = forms.DeactivateAccountForm(request.POST)
        response = {"status": "error", "errors": {}}

        if not form.is_valid():
            return JsonResponse(response, status=400)

        user = form.save()
        user.is_active = False
        user.save()
        return JsonResponse(
            {"status": "success", "message": "Account deactivated successfully."}
        )
