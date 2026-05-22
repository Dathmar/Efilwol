from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from script.combat import calculate_damage, effective_cast_time_ms, weighted_choice
from script.models import Action


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_action(name='Test Action', type='physical', base_power=10,
                cast_time=Decimal('1.0'), is_instant=False, cooldown=Decimal('1.0')):
    """Create a valid Action using objects.create() — save() calls full_clean()."""
    return Action.objects.create(
        name=name,
        description='A test action.',
        base_power=base_power,
        type=type,
        cast_time=cast_time,
        cooldown=cooldown,
        is_instant=is_instant,
    )


def make_instant_action(name='Instant Strike', base_power=10):
    return Action.objects.create(
        name=name,
        description='An instant action.',
        base_power=base_power,
        type='physical',
        cast_time=Decimal('0'),
        cooldown=Decimal('1.0'),
        is_instant=True,
    )


# ---------------------------------------------------------------------------
# TestActionValidation
# ---------------------------------------------------------------------------

class TestActionValidation(TestCase):
    """Requirement 7: Action.is_instant field and validation."""

    def test_instant_with_nonzero_cast_time_raises(self):
        """is_instant=True with cast_time=1.0 must raise ValidationError."""
        action = Action(
            name='Bad Instant',
            description='A bad instant action.',
            base_power=10,
            type='physical',
            cast_time=Decimal('1.0'),
            cooldown=Decimal('1.0'),
            is_instant=True,
        )
        with self.assertRaises(ValidationError):
            action.full_clean()

    def test_zero_cast_time_without_instant_raises(self):
        """cast_time=0 with is_instant=False must raise ValidationError."""
        action = Action(
            name='Bad Zero',
            description='A bad zero cast time action.',
            base_power=10,
            type='physical',
            cast_time=Decimal('0'),
            cooldown=Decimal('1.0'),
            is_instant=False,
        )
        with self.assertRaises(ValidationError):
            action.full_clean()

    def test_valid_instant_action_saves(self):
        """is_instant=True, cast_time=0 should save without error."""
        action = make_instant_action('Valid Instant')
        self.assertIsNotNone(action.pk)
        self.assertTrue(action.is_instant)
        self.assertEqual(action.cast_time, Decimal('0'))

    def test_valid_noninstant_action_saves(self):
        """is_instant=False, cast_time=1.5 should save without error."""
        action = make_action('Valid NonInstant', cast_time=Decimal('1.5'))
        self.assertIsNotNone(action.pk)
        self.assertFalse(action.is_instant)
        self.assertEqual(action.cast_time, Decimal('1.5'))


# ---------------------------------------------------------------------------
# TestWeightedChoice
# ---------------------------------------------------------------------------

class TestWeightedChoice(TestCase):
    """Requirement 1.5: weighted selection statistical property."""

    def test_statistical_ratio(self):
        """
        Over 1000 draws from [(1, 30), (2, 10)], action 1 should be selected
        at least 2× more often than action 2.
        """
        entries = [(1, 30), (2, 10)]
        counts = {1: 0, 2: 0}
        for _ in range(1000):
            result = weighted_choice(entries)
            counts[result] += 1
        self.assertGreaterEqual(
            counts[1],
            counts[2] * 2,
            f"Expected action 1 to be selected ≥2× more than action 2, "
            f"got {counts[1]} vs {counts[2]}",
        )

    def test_empty_raises(self):
        """weighted_choice([]) must raise ValueError."""
        with self.assertRaises(ValueError):
            weighted_choice([])

    def test_single_entry_always_selected(self):
        """weighted_choice([(42, 10)]) must always return 42."""
        for _ in range(20):
            self.assertEqual(weighted_choice([(42, 10)]), 42)


# ---------------------------------------------------------------------------
# TestCalculateDamage
# ---------------------------------------------------------------------------

class TestCalculateDamage(TestCase):
    """Requirement 4: damage formula with type matchups, crits, and speed."""

    def _attacker(self, attack=10, luck=0):
        return {'attack': attack, 'luck': luck}

    def _defender(self, defence=5, resistance=5, damage_specialization='none'):
        return {
            'defence': defence,
            'resistance': resistance,
            'damage_specialization': damage_specialization,
        }

    def test_physical_uses_defence(self):
        """Physical action: mitigation = defender.defence, not resistance."""
        action = make_action('Slash', type='physical', base_power=10)
        attacker = self._attacker(attack=10, luck=0)
        # defence=5, resistance=50 — if resistance were used, damage would be much lower
        defender = self._defender(defence=5, resistance=50, damage_specialization='none')
        damage, _, _ = calculate_damage(action, attacker, defender)
        # base_damage = max(1, 10 + 10 - 5) = 15; no crit, multiplier=1.0
        self.assertEqual(damage, 15)

    def test_nonphysical_uses_resistance(self):
        """Non-physical action: mitigation = defender.resistance, not defence."""
        action = make_action('Fireball', type='fire', base_power=10)
        attacker = self._attacker(attack=10, luck=0)
        # resistance=5, defence=50 — if defence were used, damage would be much lower
        defender = self._defender(defence=50, resistance=5, damage_specialization='none')
        damage, _, _ = calculate_damage(action, attacker, defender)
        # base_damage = max(1, 10 + 10 - 5) = 15; no crit, multiplier=1.0
        self.assertEqual(damage, 15)

    def test_type_multiplier_fire_vs_ice(self):
        """fire vs ice defender → multiplier = 2.0."""
        action = make_action('Fire Blast', type='fire', base_power=10)
        attacker = self._attacker(attack=0, luck=0)
        defender = self._defender(defence=0, resistance=0, damage_specialization='ice')
        _, _, type_mult = calculate_damage(action, attacker, defender)
        self.assertEqual(type_mult, 2.0)

    def test_type_multiplier_fire_vs_fire(self):
        """fire vs fire defender → multiplier = 0.5."""
        action = make_action('Fire Blast', type='fire', base_power=10)
        attacker = self._attacker(attack=0, luck=0)
        defender = self._defender(defence=0, resistance=0, damage_specialization='fire')
        _, _, type_mult = calculate_damage(action, attacker, defender)
        self.assertEqual(type_mult, 0.5)

    def test_type_multiplier_no_match(self):
        """fire vs physical defender → multiplier = 1.0 (no entry in table)."""
        action = make_action('Fire Blast', type='fire', base_power=10)
        attacker = self._attacker(attack=0, luck=0)
        defender = self._defender(defence=0, resistance=0, damage_specialization='physical')
        _, _, type_mult = calculate_damage(action, attacker, defender)
        self.assertEqual(type_mult, 1.0)

    def test_luck_zero_never_crits(self):
        """luck=0 → 0% crit chance → no crits over 100 attacks."""
        action = make_action('Strike', type='physical', base_power=10)
        attacker = self._attacker(attack=10, luck=0)
        defender = self._defender(defence=0)
        for _ in range(100):
            _, is_crit, _ = calculate_damage(action, attacker, defender)
            self.assertFalse(is_crit, "luck=0 should never produce a crit")

    def test_luck_100_always_crits(self):
        """luck=100 → 100% crit chance → all crits over 10 attacks."""
        action = make_action('Strike', type='physical', base_power=10)
        attacker = self._attacker(attack=10, luck=100)
        defender = self._defender(defence=0)
        for _ in range(10):
            _, is_crit, _ = calculate_damage(action, attacker, defender)
            self.assertTrue(is_crit, "luck=100 should always produce a crit")

    def test_minimum_damage_is_1(self):
        """Even with very high mitigation, final_damage must be ≥ 1."""
        action = make_action('Weak Tap', type='physical', base_power=1)
        attacker = self._attacker(attack=0, luck=0)
        # defence=9999 — would produce negative base_damage without the max(1, ...) guard
        defender = self._defender(defence=9999, resistance=9999)
        damage, _, _ = calculate_damage(action, attacker, defender)
        self.assertGreaterEqual(damage, 1)


# ---------------------------------------------------------------------------
# TestEffectiveCastTimeMs
# ---------------------------------------------------------------------------

class TestEffectiveCastTimeMs(TestCase):
    """Requirement 4.7–4.9: speed-based cast time reduction."""

    def test_instant_returns_zero(self):
        """Instant action always returns 0 regardless of speed."""
        action = make_instant_action()
        self.assertEqual(effective_cast_time_ms(action, 0), 0)
        self.assertEqual(effective_cast_time_ms(action, 50), 0)

    def test_speed_zero_returns_raw_ms(self):
        """speed=0 → no reduction → raw cast time in ms."""
        action = make_action('Slow Cast', cast_time=Decimal('2.0'))
        # raw_ms = 2000; reduction = min(0.20, 0/50) = 0
        self.assertEqual(effective_cast_time_ms(action, 0), 2000)

    def test_speed_10_returns_80_percent(self):
        """speed=10 → 20% reduction → 80% of raw ms."""
        action = make_action('Medium Cast', cast_time=Decimal('2.0'))
        # raw_ms = 2000; reduction = min(0.20, 10/50) = 0.20 → 2000 * 0.80 = 1600
        self.assertEqual(effective_cast_time_ms(action, 10), 1600)

    def test_speed_50_capped_at_80_percent(self):
        """speed=50 → reduction capped at 20% → still 80% of raw ms."""
        action = make_action('Fast Cast', cast_time=Decimal('2.0'))
        # raw_ms = 2000; reduction = min(0.20, 50/50) = 0.20 (capped) → 1600
        self.assertEqual(effective_cast_time_ms(action, 50), 1600)
