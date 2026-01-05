from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from constance import config
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.db import transaction
from django.db.models import Q
from django.utils.crypto import get_random_string
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
    organization = forms.ModelChoiceField(
        queryset=models.Organization.objects.filter(is_active=True),
        required=True,
        label=_("Organization"),
        empty_label=_("Select an organization"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password1", None)
        self.fields.pop("password2", None)

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if models.User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("An account with this email already exists")
            )

        return email

    def clean_organization(self):
        organization = self.cleaned_data.get("organization")

        if not organization:
            raise forms.ValidationError(_("This field is required"))

        if organization and not organization.is_active:
            raise forms.ValidationError(
                _("Selected organization is not active")
            )
        return organization

    def save(self, request):
        with transaction.atomic():
            user = super(AccountCreationForm, self).save(request)

            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.avatar = self.cleaned_data["avatar"]
            user.must_change_password = True

            temp_password = get_random_string(12)
            user.set_password(temp_password)
            user.save()
            self.save_permissions(user)

            # Create or update Account with organization
            account, created = models.Account.objects.get_or_create(
                user=user,
                defaults={"organization": self.cleaned_data["organization"]},
            )
            if not created:
                account.organization = self.cleaned_data["organization"]
                account.save()

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
        fields = ["avatar", "organization"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

        # Configure organization field with dynamic queryset
        active_organizations = models.Organization.objects.filter(
            is_active=True
        )
        if self.instance and self.instance.organization:
            current_org = self.instance.organization

            organizations_queryset = models.Organization.objects.filter(
                Q(is_active=True) | Q(pk=current_org.pk)
            ).distinct()
            self.fields["organization"] = forms.ModelChoiceField(
                queryset=organizations_queryset,
                required=True,
                label=_("Organization"),
                initial=current_org,
            )
        else:
            self.fields["organization"] = forms.ModelChoiceField(
                queryset=active_organizations,
                required=True,
                label=_("Organization"),
            )

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

    def clean_organization(self):
        organization = self.cleaned_data.get("organization")
        if organization and not organization.is_active:
            # Allow current organization even if inactive, but reject new inactive ones
            if self.instance and self.instance.organization != organization:
                raise forms.ValidationError(
                    _("Selected organization is not active")
                )
        return organization


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
