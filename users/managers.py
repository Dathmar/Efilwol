from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_unusable_password()
        user.save()
        user.send_password_reset_email()
        self._assign_starting_party(user)
        return user

    def _assign_starting_party(self, user):
        """Assign 3 melee + 2 ranged scripts to slots 1–5."""
        from script.models import Script
        from users.models import UserScript
        import random

        melee = list(Script.objects.filter(damage_range='melee').order_by('?')[:3])
        ranged = list(Script.objects.filter(damage_range='ranged').order_by('?')[:2])

        if len(melee) < 3 or len(ranged) < 2:
            logger.error(
                f"Insufficient scripts for starting party: "
                f"{len(melee)} melee, {len(ranged)} ranged"
            )
            raise ValueError(
                "Not enough scripts in the pool to create a valid starting party "
                f"(need 3 melee + 2 ranged, found {len(melee)} + {len(ranged)})."
            )

        for slot, script in zip([1, 2, 3], melee):
            UserScript.objects.create(
                user=user, script=script,
                party_slot=slot, in_party=True, hp=script.hp
            )
        for slot, script in zip([4, 5], ranged):
            UserScript.objects.create(
                user=user, script=script,
                party_slot=slot, in_party=True, hp=script.hp
            )

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
    MAX_PARTY_SIZE = 5

    # ----------------------------------------------------------------
    # Slot-aware methods
    # ----------------------------------------------------------------

    def assign_slot(self, user_script_id: int, slot: int, user_id: int):
        """Place a bench script into a party slot. Raises ValueError/PermissionError."""
        from users.models import UserScript
        if slot not in UserScript.ALL_SLOTS:
            raise ValueError(f"Invalid slot {slot}. Must be 1–5.")

        us = self.get(id=user_script_id)
        if us.user_id != user_id:
            raise PermissionError("UserScript does not belong to this user.")

        required = UserScript.required_range_for_slot(slot)
        if us.script.damage_range != required:
            raise ValueError(
                f"Slot {slot} requires a {required} script, "
                f"but '{us.script.name}' is {us.script.damage_range}."
            )

        # Evict current occupant if any
        self.filter(user_id=user_id, party_slot=slot).update(party_slot=None, in_party=False)

        us.party_slot = slot
        us.save()
        return us

    def swap_slot(self, slot: int, user_script_id: int, user_id: int) -> list:
        """
        Atomically swap a bench script into a slot, moving the current
        occupant to the bench. Returns get_party_state() result.
        """
        from django.db import transaction
        with transaction.atomic():
            self.assign_slot(user_script_id, slot, user_id)
        return self.get_party_state(user_id)

    def get_party_state(self, user_id: int) -> list:
        """Return list of 5 dicts, one per slot, with None for empty slots."""
        from users.models import UserScript
        occupied = {
            us.party_slot: us
            for us in self.filter(user_id=user_id, party_slot__isnull=False)
                         .select_related('script')
                         .prefetch_related('actions')
        }
        result = []
        for slot in range(1, 6):
            us = occupied.get(slot)
            if us:
                s = us.script
                result.append({
                    'slot': slot,
                    'user_script_id': us.id,
                    'name': s.name,
                    'role': s.role,
                    'role_display': s.get_role_display(),
                    'damage_range': s.damage_range,
                    'damage_range_display': s.get_damage_range_display(),
                    'damage_specialization': s.damage_specialization,
                    'damage_specialization_display': s.get_damage_specialization_display(),
                    'hp': us.hp,
                    'attack': str(s.attack),
                    'defence': str(s.defence),
                    'speed': str(s.speed),
                    'resistance': str(s.resistance),
                    'luck': str(s.luck),
                    'actions': [
                        {
                            'name': a.name,
                            'type': a.type,
                            'is_instant': a.is_instant,
                            'cast_time': a.cast_time,
                            'cooldown': a.cooldown,
                            'base_power': a.base_power,
                        }
                        for a in us.actions.all()
                    ],
                })
            else:
                result.append({
                    'slot': slot,
                    'user_script_id': None,
                    'name': None,
                    'role': None,
                    'damage_range': UserScript.required_range_for_slot(slot),
                    'actions': [],
                })
        return result

    def repair_party(self, user) -> int:
        """
        Inspect user's party, fix missing/mismatched slots.
        Returns count of slots repaired.
        """
        from users.models import UserScript
        from script.models import Script
        import random

        repaired = 0

        # Fix mismatched slots first (e.g. ranged script in melee slot)
        for us in self.filter(user=user, party_slot__isnull=False).select_related('script'):
            required = UserScript.required_range_for_slot(us.party_slot)
            if us.script.damage_range != required:
                us.party_slot = None
                us.in_party = False
                us.save()
                repaired += 1

        # Fill empty slots
        for slot in range(1, 6):
            if self.filter(user=user, party_slot=slot).exists():
                continue

            required = UserScript.required_range_for_slot(slot)

            # Try bench first
            bench_candidate = self.filter(
                user=user, party_slot__isnull=True,
                script__damage_range=required
            ).first()

            if bench_candidate:
                bench_candidate.party_slot = slot
                bench_candidate.save()
            else:
                # Create from global pool
                script = Script.objects.filter(
                    damage_range=required
                ).order_by('?').first()
                if script:
                    self.create(
                        user=user, script=script,
                        party_slot=slot, in_party=True,
                        hp=script.hp
                    )
            repaired += 1

        return repaired

    # ----------------------------------------------------------------
    # Legacy methods (kept for backward compat)
    # ----------------------------------------------------------------

    def swap_in_party(self, script_to_add_id, script_to_remove_id, user_id):
        self.remove_from_party(script_to_remove_id, user_id)
        self.add_to_party(script_to_add_id, user_id)

    def remove_from_party(self, script_id, user_id):
        us = self.get(id=script_id)
        if us.user_id != user_id:
            raise ValueError("UserScript does not belong to the user")
        us.party_slot = None
        us.save()  # save() syncs in_party automatically

    def add_to_party(self, script_id, user_id):
        """Legacy: adds to first available matching slot."""
        from users.models import UserScript
        us = self.get(id=script_id)
        if us.user_id != user_id:
            raise ValueError("UserScript does not belong to the user")

        required = us.script.damage_range
        slots = UserScript.MELEE_SLOTS if required == 'melee' else UserScript.RANGED_SLOTS
        occupied = set(
            self.filter(user_id=user_id, party_slot__in=slots)
                .values_list('party_slot', flat=True)
        )
        available = sorted(slots - occupied)
        if not available:
            raise ValueError(
                f"No available {required} slots. Remove a {required} member first."
            )
        us.party_slot = available[0]
        us.save()

