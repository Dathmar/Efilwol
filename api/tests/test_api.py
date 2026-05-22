import time
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from game.models import Stage
from script.models import Action, NPCScript, NPCScriptPoolEntry, Script, ScriptPoolEntry
from users.models import User, UserScript


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_action(name='Strike', type='physical', base_power=10,
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


def make_npc(name='Goblin'):
    return NPCScript.objects.create(
        name=name,
        description='A test NPC.',
        damage_specialization='physical',
        hp=80,
        defence=Decimal('5.0'),
        resistance=Decimal('3.0'),
        attack=Decimal('10.0'),
        speed=Decimal('5.0'),
        luck=Decimal('5.0'),
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


def make_stage(npc, order=1):
    stage = Stage.objects.create(
        name=f'Stage {order}',
        description='',
        order=order,
        is_demo=False,
        enemy_count=1,
        party_size=5,
        xp_reward=100,
    )
    stage.enemy_pool.set([npc])
    return stage


def setup_script_pool(script, actions):
    """Add actions to a script's pool with default weight 10."""
    for action in actions:
        ScriptPoolEntry.objects.get_or_create(
            script=script, action=action, defaults={'weight': 10}
        )


def setup_npc_pool(npc, actions):
    """Add actions to an NPC's pool with default weight 10."""
    for action in actions:
        NPCScriptPoolEntry.objects.get_or_create(
            npc_script=npc, action=action, defaults={'weight': 10}
        )


# ---------------------------------------------------------------------------
# TestGameAttackView
# ---------------------------------------------------------------------------

class TestGameAttackView(TestCase):
    """
    Requirements 3, 4, 6: game_attack view behaviour.
    Tests are isolated — session is set up directly without loading the game page.
    """

    def setUp(self):
        self.client = Client()

        # Create an action
        self.action = make_action('Slash', type='physical', base_power=15,
                                  cast_time=Decimal('1.0'), cooldown=Decimal('2.0'))

        # Create NPC with pool entry
        self.npc = make_npc('Goblin')
        setup_npc_pool(self.npc, [self.action])

        # Create player script with pool entries (need ≥6 for UserScript creation)
        self.script = make_script('Knight')
        self.player_actions = [
            make_action(f'Player Action {i}', cast_time=Decimal('1.0'))
            for i in range(6)
        ]
        setup_script_pool(self.script, self.player_actions)

        # Create user and UserScript
        self.user = make_user()
        self.user_script = UserScript.objects.create(
            user=self.user, script=self.script
        )

        # Build session data matching the game view's session structure
        self.party_entry = {
            'id': self.script.id,
            'script_id': self.script.id,
            'name': self.script.name,
            'hp': 100,
            'mana': 100,
            'attack': 10.0,
            'defence': 5.0,
            'resistance': 3.0,
            'speed': 5.0,
            'luck': 5.0,
            'damage_specialization': 'physical',
            'action_ids': list(self.user_script.actions.values_list('id', flat=True)),
        }
        self.enemy_entry = {
            'id': self.npc.id,
            'name': self.npc.name,
            'hp': 80,
            'attack': 10.0,
            'defence': 5.0,
            'resistance': 3.0,
            'speed': 5.0,
            'luck': 5.0,
            'damage_specialization': 'physical',
            'action_ids': [self.action.id],
        }
        self.lowlife = {'id': 0, 'name': 'Efilwol', 'hp': 150}

    def _set_session(self, cooldowns=None):
        """Write party/enemy/lowlife into the test client's session."""
        session = self.client.session
        session['party_scripts'] = [self.party_entry]
        session['enemy_scripts'] = [self.enemy_entry]
        session['lowlife'] = self.lowlife
        session['cooldowns'] = cooldowns or {}
        session.save()

    def _attack_url(self, source_id, target_id, alignment, attack_id=1):
        return reverse('api:game_attack', args=[source_id, target_id, attack_id, alignment])

    # ── Core response fields ──────────────────────────────────────────────

    def test_returns_action_name_is_crit_type_multiplier(self):
        """
        A successful attack response must include action_name, is_crit,
        and type_multiplier. Requirement 4.12, 6.1.
        """
        self._set_session()
        url = self._attack_url(self.npc.id, self.party_entry['id'], 'enemy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('action_name', data)
        self.assertIn('is_crit', data)
        self.assertIn('type_multiplier', data)
        self.assertIsNotNone(data['action_name'])
        self.assertIsInstance(data['is_crit'], bool)
        self.assertIsInstance(data['type_multiplier'], float)

    # ── Cooldown tracking ─────────────────────────────────────────────────

    def test_cooldown_written_to_session(self):
        """
        After a successful attack, session['cooldowns'] must contain the
        cooldown key for the used action. Requirement 3.3.
        """
        self._set_session()
        url = self._attack_url(self.npc.id, self.party_entry['id'], 'enemy')
        self.client.get(url)
        cooldowns = self.client.session.get('cooldowns', {})
        # At least one cooldown key should have been written
        self.assertGreater(len(cooldowns), 0)
        # The key format is 'enemy:{source_id}:{action_id}'
        expected_key = f'enemy:{self.npc.id}:{self.action.id}'
        self.assertIn(expected_key, cooldowns)

    # ── No-action (all on cooldown) ───────────────────────────────────────

    def test_no_action_when_all_on_cooldown(self):
        """
        When all action IDs are on cooldown, the response must include
        retry_after_ms > 0 and action_name=null. Requirement 3.7.
        """
        # Put the action on cooldown far in the future
        future = time.time() + 9999
        cooldowns = {f'enemy:{self.npc.id}:{self.action.id}': future}
        self._set_session(cooldowns=cooldowns)

        url = self._attack_url(self.npc.id, self.party_entry['id'], 'enemy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data['action_name'])
        self.assertGreater(data['retry_after_ms'], 0)

    # ── 404 cases ─────────────────────────────────────────────────────────

    def test_source_not_found_returns_404(self):
        """
        source_id not present in session must return 404. Requirement 4.14.
        """
        self._set_session()
        url = self._attack_url(99999, self.party_entry['id'], 'enemy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
