from allauth.account.models import EmailAddress
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = "Generates default users including superuser and staff users"

    def handle(self, *args, **kwargs):
        superuser_data = {
            "email": "admin@example.com",
            "first_name": "Administrator",
            "last_name": "Principal",
            "is_staff": True,
            "is_superuser": True,
        }

        staff_users_data = [
            {
                "email": "staff1@example.com",
                "first_name": "Staff 1",
                "last_name": "Manager",
                "is_staff": True,
            },
            {
                "email": "staff2@example.com",
                "first_name": "Staff 2",
                "last_name": "Validator",
                "is_staff": True,
            },
        ]

        default_password = "holamundo"
        users_created = 0
        users_existed = 0

        superuser = self.create_user(superuser_data, default_password)
        if superuser:
            users_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser created successfully: {superuser.email}"
                )
            )
        else:
            users_existed += 1
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser already exists: {superuser_data['email']}"
                )
            )

        for staff_data in staff_users_data:
            staff_user = self.create_user(staff_data, default_password)
            if staff_user:
                users_created += 1
                self.assign_staff_permissions(staff_user)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Staff user created successfully: {staff_user.email}"
                    )
                )
            else:
                users_existed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Staff user already exists: {staff_data['email']}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nProcess completed:\n"
                f"- Users created: {users_created}\n"
                f"- Users already existed: {users_existed}\n"
                f"- Total users processed: {users_created + users_existed}"
            )
        )

    def create_user(self, user_data, password):
        email = user_data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                email=email, password=password, **user_data
            )

            EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                primary=True,
                verified=True,
            )
            return user

        return None

    def assign_staff_permissions(self, user):
        result_permissions = Permission.objects.filter(
            codename__in=[
                "add_orderresult",
                "change_orderresult",
                "view_orderresult",
                "add_medicaltestresult",
                "change_medicaltestresult",
                "view_medicaltestresult",
            ]
        )
        user.user_permissions.add(*result_permissions)
