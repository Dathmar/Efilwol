from decimal import Decimal

from django.test import TestCase

from script.models import Action, Script, ScriptPoolEntry
from users.models import User, UserScript


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_action(name, type='physical', base_power=10,
                cast_time=Decimal('1.0'), cooldown=Decimal('1.0')):
    return Action.objects.create(
        name=name,
        description='A test action.',
        base_power=base_power,
        type=type,
        cast_time=cast_time,
        cooldown=cooldown,
        is_instant=False,
    )


def make_script(name='Knight'):
    return Script.objects.create(
        name=name,
        description='A test script.',
        damage_specialization='physical',
        hp=100,
        defence=Decimal('5.0'),
        resistance=Decimal('3.0'),
        attack=Decimal('10.0'),
        speed=Decimal('5.0'),
        luck=Decimal('5.0'),
        role='dps',
        damage_range='melee',
    )


def make_user(email='test@example.com'):
    user = User(email=email)
    user.set_password('pass123')
    user.save()
    return user


def add_pool_entries(script, actions_with_weights):
    """Add (action, weight) pairs to a script's pool."""
    for action, weight in actions_with_weights:
        ScriptPoolEntry.objects.create(script=script, action=action, weight=weight)


# ---------------------------------------------------------------------------
# TestUserScriptAssignActions
# ---------------------------------------------------------------------------

class TestUserScriptAssignActions(TestCase):
    """Requirements 2.1–2.7: UserScript action assignment at creation."""

    def setUp(self):
        self.user = make_user()
        self.script = make_script()
        # Create 8 actions for the pool
        self.actions = [make_action(f'Action {i}') for i in range(8)]

    def _fill_pool(self, actions=None, weight=10):
        """Add all (or specified) actions to the script pool with given weight."""
        if actions is None:
            actions = self.actions
        for action in actions:
            ScriptPoolEntry.objects.get_or_create(
                script=self.script, action=action,
                defaults={'weight': weight},
            )

    def test_exactly_6_actions_assigned(self):
        """Creating a UserScript from a pool of 8 assigns exactly 6 actions."""
        self._fill_pool()
        us = UserScript.objects.create(user=self.user, script=self.script)
        self.assertEqual(us.actions.count(), 6)

    def test_no_duplicates(self):
        """The 6 assigned actions must all have unique IDs."""
        self._fill_pool()
        us = UserScript.objects.create(user=self.user, script=self.script)
        action_ids = list(us.actions.values_list('id', flat=True))
        self.assertEqual(len(action_ids), len(set(action_ids)))

    def test_raises_if_pool_too_small(self):
        """Pool with only 5 entries must raise ValueError on UserScript creation."""
        for action in self.actions[:5]:
            ScriptPoolEntry.objects.create(script=self.script, action=action, weight=10)
        with self.assertRaises(ValueError):
            UserScript.objects.create(user=self.user, script=self.script)

    def test_weighted_distribution(self):
        """
        Action A (weight=30) should appear more frequently than any single
        low-weight action (weight=10) across 100 UserScript creations.

        Requirement 2.7: weighted distribution property.

        Pool must be larger than 6 so weighted selection actually discriminates.
        We use all 8 actions: 1 at weight=30, 7 at weight=10.  Only 6 of 8 are
        picked each time, so action_a's higher weight meaningfully raises its
        selection probability.
        """
        # Action A has weight 30; 7 others have weight 10 (pool size = 8 > 6)
        action_a = self.actions[0]
        low_weight_actions = self.actions[1:]  # 7 actions

        ScriptPoolEntry.objects.create(script=self.script, action=action_a, weight=30)
        for action in low_weight_actions:
            ScriptPoolEntry.objects.create(script=self.script, action=action, weight=10)

        count_a = 0
        # Track counts for each low-weight action
        low_counts = {a.id: 0 for a in low_weight_actions}

        for i in range(100):
            user = make_user(email=f'user{i}@example.com')
            us = UserScript.objects.create(user=user, script=self.script)
            assigned_ids = set(us.actions.values_list('id', flat=True))
            if action_a.id in assigned_ids:
                count_a += 1
            for a in low_weight_actions:
                if a.id in assigned_ids:
                    low_counts[a.id] += 1

        # Action A should appear more than any single low-weight action
        max_low = max(low_counts.values())
        self.assertGreater(
            count_a,
            max_low,
            f"Expected action A (weight=30) to appear more than any low-weight action. "
            f"count_a={count_a}, max_low={max_low}",
        )
