from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.users import mixins, models


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = models.User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = models.User
        fields = ("email",)


class UserSettingsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(
        max_length=30, label=_("Last name"), required=False
    )

    class Meta:
        model = models.User
        fields = ["first_name", "last_name"]


class AccountCreationForm(mixins.PermissionFormMixin, SignupForm):
    first_name = forms.CharField(max_length=30, label="First name")
    last_name = forms.CharField(max_length=30, label="Last name")
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password1", None)
        self.fields.pop("password2", None)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")

        if models.User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("An account with this email already exists")
            )

        return cleaned_data

    def save(self, request):
        with transaction.atomic():
            user = super(AccountCreationForm, self).save(request)

            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.user_type = self.cleaned_data["user_type"]
            user.avatar = self.cleaned_data["avatar"]
            user.must_change_password = True

            temp_password = models.User.objects.make_random_password()
            user.set_password(temp_password)
            user.save()
            self.save_permissions(user)

            EmailAddress.objects.get_or_create(
                user=user, email=user.email, primary=True, verified=False
            )

            if config.ENABLE_SEND_EMAIL:
                send_email_confirmation(request, user, signup=True)

            return user


class AccountUpdateForm(mixins.PermissionFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(max_length=30, label=_("Last name"))
    email = forms.EmailField(max_length=254, label=_("Email"), disabled=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = models.Account
        fields = ["avatar"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
            self.fields["avatar"].initial = self.instance.user.avatar

    def save(self, commit=True):
        account = super().save(commit=False)
        user = account.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.avatar = self.cleaned_data.get("avatar")

        user.save()
        account.save()
        self.save_permissions(user)

        return account


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = "__all__"


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = models.Organization
        fields = [
            "name",
            "description",
            "address",
            "zip_code",
            "country",
            "region",
            "subregion",
            "city",
            "phone",
            "email",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        labels = {
            "name": _("Organization Name"),
            "description": _("Description"),
            "address": _("Address"),
            "zip_code": _("Zip Code"),
            "country": _("Country"),
            "region": _("Department"),
            "subregion": _("Province"),
            "city": _("City"),
            "phone": _("Phone Number"),
            "email": _("Email Address"),
            "is_active": _("Is Active"),
        }
