from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.apps import apps
from random import randint
import uuid

from game.models import Stage
from script.models import NPCScript
from users.serializers import UserScriptSerializer


def index(request):
    stages = Stage.objects.all()
    return render(request, 'game/index.html', {'stages': stages})


def game(request, stage_id=None):
    # ── Resolve stage ────────────────────────────────────────────────────
    if stage_id:
        stage = get_object_or_404(Stage, pk=stage_id)
    else:
        # Fall back to the first demo stage, then any stage
        stage = Stage.objects.filter(is_demo=True).order_by('order').first()
        if not stage:
            stage = Stage.objects.order_by('order').first()

    if not stage:
        messages.warning(request, 'No stages found. Run: python manage.py seed_stages')
        return redirect('game:index')

    # ── Auth check ───────────────────────────────────────────────────────
    if not stage.is_demo and not request.user.is_authenticated:
        messages.info(request, 'Please log in to play this stage.')
        return redirect('login')

    # ── Enemies ──────────────────────────────────────────────────────────
    enemies_qs = stage.get_enemies()
    if not enemies_qs:
        # Fallback: any NPC
        enemies_qs = list(NPCScript.objects.order_by('?')[:stage.enemy_count])

    if not enemies_qs:
        messages.warning(request, 'No enemies found. Run: python manage.py populate_game_data')
        return redirect('game:index')

    enemy_session = [
        {
            'id': npc.id,
            'name': npc.name,
            'hp': npc.hp,
            'attack': float(npc.attack),
            'defence': float(npc.defence),
            'resistance': float(npc.resistance),
            'speed': float(npc.speed),
            'luck': float(npc.luck),
            'damage_specialization': npc.damage_specialization,
            'action_ids': list(npc.pool_entries.values_list('action_id', flat=True)),
        }
        for npc in enemies_qs
    ]

    # ── Party ────────────────────────────────────────────────────────────
    if request.user.is_authenticated:
        UserScript = apps.get_model('users', 'UserScript')
        party_scripts = UserScript.objects.filter(
            user=request.user, in_party=True
        ).select_related('script').order_by('party_slot')[:stage.party_size]
        serialized_party = UserScriptSerializer(party_scripts, many=True)
        party_session = [
            {
                'id': p['id'],           # UserScript PK — unique per slot
                'script_id': p['script_id'],
                'name': p['script_name'],
                'hp': p['hp'],
                'mana': p['mana'],
                'attack': float(us.script.attack),
                'defence': float(us.script.defence),
                'resistance': float(us.script.resistance),
                'speed': float(us.script.speed),
                'luck': float(us.script.luck),
                'damage_specialization': us.script.damage_specialization,
                'action_ids': p['action_ids'],
            }
            for p, us in zip(serialized_party.data, party_scripts)
        ]
    else:
        # Demo: generate a throwaway party from the stage's demo pool
        demo_scripts = stage.get_demo_party()
        party_scripts = None
        party_session = [
            {
                'id': s.id,
                'script_id': s.id,
                'name': s.name,
                'hp': s.hp,
                'mana': 100,
                'attack': float(s.attack),
                'defence': float(s.defence),
                'resistance': float(s.resistance),
                'speed': float(s.speed),
                'luck': float(s.luck),
                'damage_specialization': s.damage_specialization,
                # Use pool entries directly — demo scripts have no UserScript
                'action_ids': list(s.pool_entries.values_list('action_id', flat=True)[:6]),
            }
            for s in demo_scripts
        ]

    # ── Lowlife (Efilwol) ────────────────────────────────────────────────
    lowlife = {'id': 0, 'name': 'Efilwol', 'hp': randint(100, 200)}

    # ── Heals (hardcoded for now, will come from Action model later) ─────
    healz = [
        {'id': 1, 'name': 'Quick Heal',   'target': 'Single', 'min': 10, 'max': 20,  'cast_time': 2000},
        {'id': 2, 'name': 'Greater Heal', 'target': 'Single', 'min': 30, 'max': 60,  'cast_time': 6000},
    ]

    # ── Session ──────────────────────────────────────────────────────────
    request.session['cooldowns'] = {}
    request.session['enemy_scripts'] = enemy_session
    request.session['party_scripts'] = party_session
    request.session['lowlife'] = lowlife
    request.session['healz'] = healz

    context = {
        'stage': stage,
        'enemy_scripts': enemy_session,
        'party_scripts': party_scripts if request.user.is_authenticated else _demo_party_context(party_session),
        'lowlife': lowlife,
        'healz': healz,
        'game_id': str(uuid.uuid4()),
        'game_hash': str(uuid.uuid4()).replace('-', ''),
        'is_demo': stage.is_demo,
        # Anon users always get confirm mode; auth'd users use their preference
        'confirm_cast_cancel': request.user.preferences.confirm_cast_cancel if request.user.is_authenticated else True,
    }

    return render(request, 'game/game.html', context)


# ── Helpers ──────────────────────────────────────────────────────────────────

class _DemoPartyScript:
    """Thin wrapper so demo party dicts work with the same template as UserScript."""
    def __init__(self, data):
        self.hp = data['hp']
        self.script = _DemoScript(data)

    def __repr__(self):
        return f'<DemoPartyScript {self.script.name}>'


class _DemoScript:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.role = 'dps'
        self.damage_range = 'melee'


def _demo_party_context(party_session):
    return [_DemoPartyScript(p) for p in party_session]
