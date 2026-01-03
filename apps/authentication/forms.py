from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.users import models as user_models


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label="First Name",
        widget=forms.TextInput(attrs={"placeholder": _("First Name")}),
    )
    last_name = forms.CharField(
        max_length=30,
        label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": _("Last Name")}),
    )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        return user


class DeactivateAccountForm(forms.Form):
    email = forms.EmailField(max_length=254, label=_("Email"), required=True)

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        user = user_models.User.objects.filter(email=email).first()

        if not user:
            raise forms.ValidationError(_("The email address is not registered with us."))

        user.is_active = False
        user.save()

        return user
