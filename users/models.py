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

    def add_random_script(self, in_party=False):
        script_model = apps.get_model('script', 'Script')
        script = script_model.objects.order_by('?').first()
        if in_party:
            current = UserScript.objects.filter(user=self, in_party=True).count()
            if current >= UserScript.objects.MAX_PARTY_SIZE:
                raise ValueError(
                    f"Party is full ({UserScript.objects.MAX_PARTY_SIZE} members max)."
                )
        UserScript.objects.create(user=self, script=script, in_party=in_party)

    @property
    def preferences(self):
        prefs, _ = UserPreferences.objects.get_or_create(user=self)
        return prefs

    def __str__(self):
        return self.email


class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='_preferences')

    confirm_cast_cancel = models.BooleanField(
        default=True,
        verbose_name='Confirm before cancelling a cast',
        help_text=(
            'When enabled, clicking a new heal target while casting shows an Abort button '
            'instead of immediately cancelling. Useful if you want to avoid accidental interruptions.'
        ),
    )

    class Meta:
        verbose_name = 'User Preferences'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f'{self.user.email} — preferences'


class UserScript(models.Model):
    MELEE_SLOTS = frozenset({1, 2, 3})
    RANGED_SLOTS = frozenset({4, 5})
    ALL_SLOTS = frozenset({1, 2, 3, 4, 5})

    @staticmethod
    def required_range_for_slot(slot: int) -> str:
        if slot in UserScript.MELEE_SLOTS:
            return 'melee'
        if slot in UserScript.RANGED_SLOTS:
            return 'ranged'
        raise ValueError(f"Invalid slot {slot}. Must be 1–5.")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    script = models.ForeignKey('script.Script', on_delete=models.CASCADE)
    in_party = models.BooleanField(default=False)
    party_slot = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Party position 1–5, or null if on bench. Slots 1–3=melee, 4–5=ranged."
    )
    hp = models.IntegerField(default=100)
    mana = models.IntegerField(default=100)

    actions = models.ManyToManyField('script.Action', blank=True)

    objects = UserScriptManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'party_slot'],
                condition=models.Q(party_slot__isnull=False),
                name='unique_party_slot_per_user',
            )
        ]

    def assign_actions(self):
        """
        Draw 6 unique actions from the associated script's pool using weighted
        random selection (via weighted_choice from script.combat).

        Raises:
            ValueError: if the script's pool has fewer than 6 entries.
        """
        from script.combat import weighted_choice

        entries = list(self.script.pool_entries.select_related('action').all())
        if len(entries) < 6:
            raise ValueError(
                f"Script '{self.script.name}' has only {len(entries)} action(s) in its pool "
                f"(need at least 6)."
            )

        # Build (action_id, weight) tuples for weighted_choice
        pool = [(e.action_id, e.weight) for e in entries]
        action_map = {e.action_id: e.action for e in entries}

        # Weighted draw with deduplication
        seen = set()
        unique = []
        # Draw up to len(pool) times to get 6 unique actions
        for _ in range(len(pool) * 10):
            if len(unique) == 6:
                break
            action_id = weighted_choice(pool)
            if action_id not in seen:
                seen.add(action_id)
                unique.append(action_map[action_id])

        # Fallback: fill remaining slots from the pool in order if weighted draws
        # didn't yield 6 unique actions (e.g. pool has exactly 6 entries)
        if len(unique) < 6:
            remaining = [action_map[aid] for aid, _ in pool if aid not in seen]
            unique.extend(remaining[:6 - len(unique)])

        self.actions.set(unique)

    def save(self, *args, **kwargs):
        # Keep in_party in sync with party_slot
        self.in_party = self.party_slot is not None
        # Track whether this is a new instance before saving
        is_adding = self._state.adding
        super().save(*args, **kwargs)
        # Assign actions on creation (after save so PK exists for M2M)
        if is_adding:
            self.assign_actions()

    def __str__(self):
        return f"{self.user.email} - {self.script.name}"


class Suggestion(models.Model):
    class Category(models.TextChoices):
        GAMEPLAY = 'gameplay', 'Gameplay'
        UI = 'ui', 'UI / Design'
        BUG = 'bug', 'Bug Report'
        CONTENT = 'content', 'Content'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggestions')
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_category_display()}] {self.title} — {self.user.email}'
