from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_unusable_password()
        user.save()
        user.send_password_reset_email()

        for _ in range(5):
            user.add_random_script()

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, **extra_fields)

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the email address by lowercasing it.
        """
        return email.lower()

    def get_by_natural_key(self, email):
        return self.get(email=self.normalize_email(email))

class UserScriptManager(models.Manager):
    def swap_in_party(self, script_to_add_id, script_to_remove_id, user_id):
        """
        Swap the in_party status of a UserScript object.
        """
        self.remove_from_party(script_to_remove_id, user_id)
        self.add_to_party(script_to_add_id, user_id)

    def remove_from_party(self, script_id, user_id):
        """
        Remove a UserScript object from the party.
        """
        script = self.get(id=script_id)

        if script.user.id != user_id:
            raise ValueError("UserScript does not belong to the user")

        script.in_party = False
        script.save()

    def add_to_party(self, script_id, user_id):
        """
        Add a UserScript object to the party.
        """
        script = self.get(id=script_id)

        if script.user.id != user_id:
            raise ValueError("UserScript does not belong to the user")

        script.in_party = True
        script.save()

