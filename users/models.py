from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.apps import apps

from base.emailing import send_password_reset

from .managers import UserManager

import logging
from .managers import UserScriptManager

logger = logging.getLogger('console_only')


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def send_password_reset_email(self):
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self)
        logger.info(f"Password reset token: {token}")
        send_password_reset(self, token)

    def validate_password_reset_token(self, token):
        token_generator = PasswordResetTokenGenerator()
        return token_generator.check_token(self, token)

    def add_random_script(self):
        script_model = apps.get_model('script', 'Script')
        script = script_model.objects.order_by('?').first()
        UserScript.objects.create(user=self, script=script)

    def __str__(self):
        return self.email


class UserScript(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    script = models.ForeignKey('script.Script', on_delete=models.CASCADE)  # eventually we should just replicate the base script required details to the user level.
    in_party = models.BooleanField(default=False)
    hp = models.IntegerField(default=100)
    mana = models.IntegerField(default=100)

    objects = UserScriptManager()

    def __str__(self):
        return f"{self.user.email} - {self.script.name}"
