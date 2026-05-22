import logging
import time

from django.http import JsonResponse

from script.combat import calculate_damage, effective_cast_time_ms, weighted_choice
from script.models import Action, NPCScriptPoolEntry

logger = logging.getLogger(__name__)


def game_attack(request, source_id, target_id, attack_id, script_alignment):
    """
    Execute a single attack from a combatant.

    script_alignment: 'player' or 'enemy' — identifies the SOURCE combatant type.
    target_id of 0 means the Efilwol lowlife character.
    attack_id is a legacy URL parameter and is not used for action selection.
    """
    # ── 1. Resolve source and target from session ─────────────────────────
    if script_alignment == 'enemy':
        source = get_script_by_id(request.session.get('enemy_scripts', []), source_id)
        target_list = request.session.get('party_scripts', [])
    else:
        source = get_script_by_id(request.session.get('party_scripts', []), source_id)
        target_list = request.session.get('enemy_scripts', [])

    if not source:
        return JsonResponse({'error': 'Source not found', 'source_id': source_id}, status=404)

    target = (
        request.session.get('lowlife')
        if target_id == 0
        else get_script_by_id(target_list, target_id)
    )

    if not target:
        return JsonResponse({'error': 'Target not found', 'target_id': target_id}, status=404)

    # ── 2. Resolve available action IDs (respecting cooldowns) ───────────
    prefix = 'enemy' if script_alignment == 'enemy' else 'player'
    cooldowns = request.session.get('cooldowns', {})
    now = time.time()

    action_ids = source.get('action_ids')

    # Fallback: action_ids missing from session — query DB and log a warning
    if action_ids is None:
        logger.warning(
            "action_ids missing from session for %s source_id=%s — falling back to DB lookup",
            script_alignment,
            source_id,
        )
        if script_alignment == 'player':
            from users.models import UserScript
            try:
                us = UserScript.objects.get(script_id=source_id, user=request.user)
                action_ids = list(us.actions.values_list('id', flat=True))
            except (UserScript.DoesNotExist, Exception):
                action_ids = []
        else:
            action_ids = list(
                NPCScriptPoolEntry.objects
                .filter(npc_script_id=source_id)
                .values_list('action_id', flat=True)
            )

    available = [
        aid for aid in action_ids
        if cooldowns.get(f'{prefix}:{source_id}:{aid}', 0) <= now
    ]

    # ── 3. Handle no-action case (all on cooldown) ────────────────────────
    if not available:
        if action_ids:
            expiries = [cooldowns.get(f'{prefix}:{source_id}:{aid}', 0) for aid in action_ids]
            earliest = min(expiries)
        else:
            earliest = now
        retry_ms = max(0, round((earliest - now) * 1000))
        return JsonResponse({
            'damage_done': 0,
            'cast_time': 0,
            'cool_down': 0,
            'action_name': None,
            'is_crit': False,
            'type_multiplier': 1.0,
            'retry_after_ms': retry_ms,
        })

    # ── 4. Weighted action selection ──────────────────────────────────────
    if script_alignment == 'enemy':
        # Use pool weights from NPCScriptPoolEntry
        entries = list(
            NPCScriptPoolEntry.objects
            .filter(npc_script_id=source_id, action_id__in=available)
            .values_list('action_id', 'weight')
        )
        # Fall back to equal weights if no entries found (shouldn't happen)
        if not entries:
            entries = [(aid, 10) for aid in available]
    else:
        # Player scripts: equal weights — weighted selection was applied at assignment time
        entries = [(aid, 10) for aid in available]

    action_id = weighted_choice(entries)
    action = Action.objects.get(id=action_id)

    # ── 5. Compute damage ─────────────────────────────────────────────────
    damage, is_crit, type_mult = calculate_damage(action, source, target)

    # ── 6. Compute cast time with speed reduction ─────────────────────────
    cast_ms = effective_cast_time_ms(action, source.get('speed', 0))
    cool_ms = int(action.cooldown * 1000)

    # ── 7. Record cooldown in session ─────────────────────────────────────
    cooldowns[f'{prefix}:{source_id}:{action_id}'] = now + float(action.cooldown)
    request.session['cooldowns'] = cooldowns
    request.session.modified = True

    return JsonResponse({
        'damage_done': damage,
        'cast_time': cast_ms,
        'cool_down': cool_ms,
        'action_name': action.name,
        'is_crit': is_crit,
        'type_multiplier': type_mult,
        'retry_after_ms': 0,
    })


def get_script_by_id(script_list, script_id):
    for script in script_list:
        if int(script.get('id', -1)) == int(script_id):
            return script
    return None
