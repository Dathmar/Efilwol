from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from game.models import Stage
from script.models import Script, NPCScript, Action, ScriptPoolEntry, NPCScriptPoolEntry
from users.models import User, UserScript


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_action(name='Basic Attack'):
    """Create or retrieve a valid Action with cast_time=1.0 (non-instant)."""
    return Action.objects.get_or_create(
        name=name,
        defaults=dict(
            description='A basic attack',
            base_power=20,
            type='physical',
            cast_time=Decimal('1.0'),
            cooldown=Decimal('1.0'),
            is_instant=False,
        )
    )[0]


def make_npc(name='Goblin', hp=80):
    npc = NPCScript.objects.create(
        name=name,
        description='A goblin',
        damage_specialization='physical',
        hp=hp,
        defence=Decimal('5.0'),
        resistance=Decimal('3.0'),
        attack=Decimal('15.0'),
        speed=Decimal('8.0'),
        luck=Decimal('5.0'),
    )
    # Give the NPC at least one pool entry so the attack API can select an action
    action = make_action(f'{name} Strike')
    NPCScriptPoolEntry.objects.get_or_create(npc_script=npc, action=action, defaults={'weight': 10})
    return npc


def make_script(name='Knight', role='tank', damage_range='melee', hp=120):
    """Create a Script WITHOUT pool entries. Use make_script_with_pool when
    you need to create a UserScript from it."""
    return Script.objects.create(
        name=name,
        description='A knight',
        damage_specialization='physical',
        hp=hp,
        defence=Decimal('12.0'),
        resistance=Decimal('6.0'),
        attack=Decimal('15.0'),
        speed=Decimal('5.0'),
        luck=Decimal('5.0'),
        role=role,
        damage_range=damage_range,
    )


def make_script_with_pool(name='Knight', role='tank', damage_range='melee', hp=120,
                          pool_size=6):
    """Create a Script with pool_size pool entries so UserScript creation works."""
    script = make_script(name=name, role=role, damage_range=damage_range, hp=hp)
    for i in range(pool_size):
        action = make_action(f'{name} Action {i}')
        ScriptPoolEntry.objects.get_or_create(
            script=script, action=action, defaults={'weight': 10}
        )
    return script


def make_user(email='test@test.com', password='pass123'):
    """
    Create a user bypassing the custom manager's side effects
    (email sending, add_random_script) so tests stay isolated.
    """
    user = User(email=email)
    user.set_password(password)
    user.save()
    return user


def make_stage(order=1, is_demo=False, npcs=None, scripts=None, party_size=5):
    stage = Stage.objects.create(
        name=f'Stage {order}',
        description='Test stage',
        order=order,
        is_demo=is_demo,
        enemy_count=3,
        party_size=party_size,
        xp_reward=0 if is_demo else 100,
    )
    if npcs:
        stage.enemy_pool.set(npcs)
    if scripts:
        stage.demo_party_pool.set(scripts)
    return stage


# ---------------------------------------------------------------------------
# Game view tests
# ---------------------------------------------------------------------------

class GameViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.script = make_script_with_pool()
        self.user = make_user()
        self.npc1 = make_npc('Goblin')
        self.npc2 = make_npc('Orc', hp=100)
        self.npc3 = make_npc('Troll', hp=150)
        self.stage = make_stage(order=1, is_demo=False, npcs=[self.npc1, self.npc2, self.npc3])
        self.demo_stage = make_stage(
            order=0, is_demo=True,
            npcs=[self.npc1, self.npc2, self.npc3],
            scripts=[self.script]
        )
        self.user_script = UserScript.objects.create(
            user=self.user, script=self.script, party_slot=1, hp=120
        )

    def test_game_index_loads(self):
        response = self.client.get(reverse('game:index'))
        self.assertEqual(response.status_code, 200)

    def test_index_shows_stages(self):
        response = self.client.get(reverse('game:index'))
        self.assertIn('stages', response.context)
        self.assertEqual(response.context['stages'].count(), 2)

    def test_demo_stage_accessible_without_login(self):
        url = reverse('game:game_stage', args=[self.demo_stage.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_demo_stage_context_has_is_demo_true(self):
        url = reverse('game:game_stage', args=[self.demo_stage.id])
        response = self.client.get(url)
        self.assertTrue(response.context['is_demo'])

    def test_auth_stage_redirects_anon(self):
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_game_requires_login(self):
        # /play/ with no demo stage falls back — but we have a demo stage so it loads
        # Test the explicit auth stage instead
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_game_loads_when_logged_in(self):
        self.client.force_login(self.user)
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_game_context_has_three_enemies(self):
        self.client.force_login(self.user)
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertEqual(len(response.context['enemy_scripts']), 3)

    def test_game_context_has_party(self):
        self.client.force_login(self.user)
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertEqual(len(response.context['party_scripts']), 1)

    def test_demo_party_generated_for_anon(self):
        url = reverse('game:game_stage', args=[self.demo_stage.id])
        response = self.client.get(url)
        # Demo party comes from demo_party_pool (1 script seeded)
        self.assertGreater(len(response.context['party_scripts']), 0)

    def test_game_context_lowlife_is_efilwol(self):
        self.client.force_login(self.user)
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        lowlife = response.context['lowlife']
        self.assertEqual(lowlife['name'], 'Efilwol')
        self.assertGreaterEqual(lowlife['hp'], 100)
        self.assertLessEqual(lowlife['hp'], 200)

    def test_game_context_has_game_id_and_hash(self):
        self.client.force_login(self.user)
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertIn('game_id', response.context)
        self.assertIn('game_hash', response.context)

    def test_game_sets_session_enemy_scripts(self):
        self.client.force_login(self.user)
        self.client.get(reverse('game:game_stage', args=[self.stage.id]))
        self.assertEqual(len(self.client.session['enemy_scripts']), 3)

    def test_game_sets_session_party_scripts(self):
        self.client.force_login(self.user)
        self.client.get(reverse('game:game_stage', args=[self.stage.id]))
        self.assertEqual(len(self.client.session['party_scripts']), 1)

    def test_party_session_id_matches_script_id(self):
        self.client.force_login(self.user)
        self.client.get(reverse('game:game_stage', args=[self.stage.id]))
        party = self.client.session['party_scripts']
        self.assertEqual(party[0]['id'], self.script.id)

    def test_game_context_has_healz(self):
        self.client.force_login(self.user)
        url = reverse('game:game_stage', args=[self.stage.id])
        response = self.client.get(url)
        self.assertIn('healz', response.context)
        self.assertGreater(len(response.context['healz']), 0)


# ---------------------------------------------------------------------------
# Attack API tests
# ---------------------------------------------------------------------------

class AttackAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.script = make_script_with_pool()
        self.user = make_user()
        self.npc1 = make_npc('Goblin')
        self.npc2 = make_npc('Orc', hp=100)
        self.npc3 = make_npc('Troll', hp=150)
        self.stage = make_stage(order=1, is_demo=False, npcs=[self.npc1, self.npc2, self.npc3])
        self.user_script = UserScript.objects.create(
            user=self.user, script=self.script, party_slot=1, hp=120
        )
        self.client.force_login(self.user)
        self.client.get(reverse('game:game_stage', args=[self.stage.id]))

    def _enemy_id(self):
        return self.client.session['enemy_scripts'][0]['id']

    def _party_id(self):
        return self.client.session['party_scripts'][0]['id']

    def test_enemy_attacks_player(self):
        url = reverse('api:game_attack', args=[self._enemy_id(), self._party_id(), 1, 'enemy'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('damage_done', data)
        self.assertIn('cast_time', data)
        self.assertIn('cool_down', data)

    def test_player_attacks_enemy(self):
        url = reverse('api:game_attack', args=[self._party_id(), self._enemy_id(), 1, 'player'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('damage_done', response.json())

    def test_damage_is_positive(self):
        url = reverse('api:game_attack', args=[self._enemy_id(), self._party_id(), 1, 'enemy'])
        data = self.client.get(url).json()
        self.assertGreater(data['damage_done'], 0)

    def test_cast_time_is_positive(self):
        url = reverse('api:game_attack', args=[self._enemy_id(), self._party_id(), 1, 'enemy'])
        data = self.client.get(url).json()
        self.assertGreater(data['cast_time'], 0)

    def test_unknown_source_returns_404(self):
        url = reverse('api:game_attack', args=[99999, self._party_id(), 1, 'enemy'])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_unknown_target_returns_404(self):
        url = reverse('api:game_attack', args=[self._enemy_id(), 99999, 1, 'enemy'])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_player_can_attack_lowlife(self):
        """target_id=0 is the Efilwol lowlife character."""
        url = reverse('api:game_attack', args=[self._party_id(), 0, 1, 'player'])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_enemy_can_attack_lowlife(self):
        """Enemies should be able to target Efilwol (target_id=0)."""
        enemy_id = self._enemy_id()
        url = reverse('api:game_attack', args=[enemy_id, 0, 1, 'enemy'])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_attack_without_session_returns_404(self):
        """No game page loaded means no session data — should fail gracefully."""
        fresh = Client()
        fresh.force_login(self.user)
        url = reverse('api:game_attack', args=[1, 2, 1, 'enemy'])
        self.assertEqual(fresh.get(url).status_code, 404)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class StageModelTests(TestCase):
    def setUp(self):
        self.npc = make_npc()
        self.script = make_script()
        self.stage = make_stage(order=1, is_demo=True, npcs=[self.npc], scripts=[self.script])

    def test_str_includes_name_and_demo_tag(self):
        self.assertIn('DEMO', str(self.stage))
        self.assertIn(self.stage.name, str(self.stage))

    def test_get_enemies_returns_correct_count(self):
        self.stage.enemy_count = 1
        self.stage.save()
        enemies = self.stage.get_enemies()
        self.assertEqual(len(enemies), 1)

    def test_get_demo_party_returns_scripts(self):
        self.stage.party_size = 1
        self.stage.save()
        party = self.stage.get_demo_party()
        self.assertEqual(len(party), 1)
        self.assertIsInstance(party[0], type(self.script))

    def test_party_size_default_is_five(self):
        stage = make_stage(order=99)
        self.assertEqual(stage.party_size, 5)

    def test_script_str_contains_name(self):
        self.assertIn('Knight', str(make_script()))

    def test_npc_str_is_name(self):
        self.assertEqual(str(make_npc()), 'Goblin')

    def test_action_str_contains_name(self):
        self.assertIn('Basic Attack', str(make_action()))

    def test_user_script_str(self):
        script = make_script_with_pool()
        user = make_user()
        us = UserScript.objects.create(user=user, script=script, party_slot=1, hp=100)
        self.assertIn('test@test.com', str(us))
        self.assertIn('Knight', str(us))


class UserScriptTests(TestCase):
    def setUp(self):
        self.script1 = make_script_with_pool('Knight', 'tank', 'melee', hp=120)
        self.script2 = make_script_with_pool('Archer', 'dps', 'ranged', hp=80)
        self.user = make_user()

    def test_user_can_have_multiple_scripts(self):
        UserScript.objects.create(user=self.user, script=self.script1, party_slot=1, hp=120)
        UserScript.objects.create(user=self.user, script=self.script2, party_slot=4, hp=80)
        self.assertEqual(UserScript.objects.filter(user=self.user).count(), 2)

    def test_in_party_filter(self):
        UserScript.objects.create(user=self.user, script=self.script1, party_slot=1, hp=120)
        UserScript.objects.create(user=self.user, script=self.script2, hp=80)  # bench
        party = UserScript.objects.filter(user=self.user, in_party=True)
        self.assertEqual(party.count(), 1)
        self.assertEqual(party.first().script.name, 'Knight')

    def test_add_random_script(self):
        self.user.add_random_script(in_party=False)
        self.assertEqual(UserScript.objects.filter(user=self.user).count(), 1)

    def test_swap_in_party(self):
        us1 = UserScript.objects.create(user=self.user, script=self.script1, party_slot=1, hp=120)
        us2 = UserScript.objects.create(user=self.user, script=self.script2, hp=80)  # bench
        # Use assign_slot to move us2 into slot 4 (ranged)
        UserScript.objects.assign_slot(us2.id, 4, self.user.id)
        us2.refresh_from_db()
        self.assertEqual(us2.party_slot, 4)
        self.assertTrue(us2.in_party)


# ---------------------------------------------------------------------------
# TestGameViewSessionReset
# ---------------------------------------------------------------------------

class TestGameViewSessionReset(TestCase):
    """Requirement 3.1: game view resets session['cooldowns'] to {} on load."""

    def setUp(self):
        self.client = Client()
        self.script = make_script_with_pool('Warrior')
        self.user = make_user(email='reset@test.com')
        self.npc = make_npc('Slime')
        self.stage = make_stage(order=10, is_demo=False, npcs=[self.npc])
        UserScript.objects.create(user=self.user, script=self.script, party_slot=1, hp=100)
        self.client.force_login(self.user)

    def test_cooldowns_reset_on_game_view(self):
        """
        Loading the game view must reset session['cooldowns'] to {}, even if
        it previously contained stale cooldown data.
        """
        # Seed the session with stale cooldown data
        session = self.client.session
        session['cooldowns'] = {'old_key': 999999}
        session.save()

        # Load the game view — this should reset cooldowns
        self.client.get(reverse('game:game_stage', args=[self.stage.id]))

        # Cooldowns must now be an empty dict
        self.assertEqual(self.client.session.get('cooldowns'), {})
