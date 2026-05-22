# Design Document: Script Attack System

## Overview

This feature replaces the placeholder attack API with a fully data-driven combat pipeline. The key changes are: two new through models for weighted action pools, `is_instant` validation on `Action`, action assignment at `UserScript` creation, session-based cooldown tracking, a real damage formula with type matchups and crits, speed-based cast time reduction, and UI display of assigned actions on the party and script management pages.

---

## Model Changes

### 1. `Action` — add `is_instant`

```python
is_instant = models.BooleanField(default=False)

def clean(self):
    if self.is_instant and self.cast_time != 0:
        raise ValidationError("Instant actions must have cast_time = 0.")
    if not self.is_instant and self.cast_time == 0:
        raise ValidationError("cast_time can only be 0 if is_instant is True.")

def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)
```

Migration: add `is_instant` as nullable first, run data migration to set `is_instant=True` where `cast_time=0`, then make non-nullable.

### 2. Remove `action_pool` from `BaseScript`

`BaseScript.action_pool` is removed. Two concrete through models replace it:

```python
# script/models.py

class ScriptPoolEntry(models.Model):
    script = models.ForeignKey(Script, on_delete=models.CASCADE, related_name='pool_entries')
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = ('script', 'action')

class NPCScriptPoolEntry(models.Model):
    npc_script = models.ForeignKey(NPCScript, on_delete=models.CASCADE, related_name='pool_entries')
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = ('npc_script', 'action')
```

`Script.action_pool` and `NPCScript.action_pool` become:

```python
# On Script:
action_pool = models.ManyToManyField(Action, through='ScriptPoolEntry', blank=True)

# On NPCScript:
action_pool = models.ManyToManyField(Action, through='NPCScriptPoolEntry', blank=True)
```

Since `BaseScript` is abstract, the M2M fields must be declared on the concrete models, not the abstract base.

### 3. `UserScript.actions` — populated at creation

The existing `actions = ManyToManyField(Action, blank=True)` stays. A new `assign_actions()` method on `UserScript` (or in the manager) handles weighted selection:

```python
def assign_actions(self):
    """Draw 6 unique actions from the script's pool using weighted selection."""
    entries = list(self.script.pool_entries.select_related('action'))
    if len(entries) < 6:
        raise ValueError(
            f"Script '{self.script.name}' has only {len(entries)} actions in its pool "
            f"(need at least 6)."
        )
    weights = [e.weight for e in entries]
    actions = [e.action for e in entries]
    selected = random.choices(actions, weights=weights, k=len(actions))
    # Deduplicate while preserving weighted order
    seen, unique = set(), []
    for a in selected:
        if a.id not in seen:
            seen.add(a.id)
            unique.append(a)
        if len(unique) == 6:
            break
    # Fallback: if weighted choices didn't yield 6 unique, fill from remainder
    if len(unique) < 6:
        remaining = [a for a in actions if a.id not in seen]
        unique.extend(remaining[:6 - len(unique)])
    self.actions.set(unique)
```

`UserScript.save()` calls `assign_actions()` only on creation (when `self.pk is None`), after the instance is saved (so the M2M can be set).

---

## Weighted Selection Utility

A shared utility function used by both `UserScript.assign_actions()` and the attack API:

```python
# script/combat.py

import random

def weighted_choice(entries):
    """Select one entry from a list of (action, weight) tuples."""
    total = sum(w for _, w in entries)
    r = random.uniform(0, total)
    cumulative = 0
    for action, weight in entries:
        cumulative += weight
        if r <= cumulative:
            return action
    return entries[-1][0]  # fallback
```

---

## Type Matchup Table

Defined as a module-level constant in `script/combat.py`:

```python
TYPE_MATCHUPS = {
    ('fire',      'ice'):       2.0,
    ('fire',      'fire'):      0.5,
    ('fire',      'water'):     0.5,
    ('ice',       'fire'):      2.0,
    ('ice',       'ice'):       0.5,
    ('ice',       'earth'):     1.5,
    ('lightning', 'water'):     2.0,
    ('lightning', 'earth'):     0.5,
    ('lightning', 'lightning'): 0.5,
    ('water',     'fire'):      1.5,
    ('water',     'lightning'): 0.5,
    ('water',     'water'):     0.5,
    ('earth',     'lightning'): 1.5,
    ('earth',     'earth'):     0.5,
    ('poison',    'earth'):     1.5,
    ('poison',    'poison'):    0.5,
    ('holy',      'dark'):      2.0,
    ('holy',      'necrotic'):  2.0,
    ('holy',      'holy'):      0.5,
    ('dark',      'holy'):      2.0,
    ('dark',      'dark'):      0.5,
    ('necrotic',  'holy'):      1.5,
    ('physical',  'physical'):  1.0,
}
```

---

## Damage Calculation

Also in `script/combat.py`:

```python
def calculate_damage(action, attacker, defender):
    """
    Returns (damage, is_crit, type_multiplier).
    attacker/defender are dicts with keys: attack, defence, resistance, luck,
    damage_specialization.
    """
    import random

    # Mitigation
    if action.type == 'physical':
        mitigation = float(attacker.get('defence', 0))  # Note: mitigation is defender's
    else:
        mitigation = float(defender.get('resistance', 0))

    # Correct: mitigation comes from defender
    if action.type == 'physical':
        mitigation = float(defender.get('defence', 0))
    else:
        mitigation = float(defender.get('resistance', 0))

    base_damage = max(1, action.base_power + float(attacker.get('attack', 0)) - mitigation)

    # Type matchup
    type_multiplier = TYPE_MATCHUPS.get(
        (action.type, defender.get('damage_specialization', 'none')), 1.0
    )

    # Crit
    crit_chance = float(attacker.get('luck', 0)) / 100
    is_crit = random.random() < crit_chance
    crit_multiplier = 1.5 if is_crit else 1.0

    final_damage = max(1, round(base_damage * type_multiplier * crit_multiplier))
    return final_damage, is_crit, type_multiplier


def effective_cast_time_ms(action, attacker_speed):
    """Apply speed reduction. Instant actions always return 0."""
    if action.is_instant:
        return 0
    raw_ms = int(action.cast_time * 1000)
    reduction = min(0.20, float(attacker_speed) / 50)
    return round(raw_ms * (1 - reduction))
```

---

## Session Structure Changes

`game/views.py` adds `action_ids` and stats to each session entry:

```python
# party_scripts entry (per UserScript):
{
    'id': script.id,
    'script_id': script.id,
    'name': script.name,
    'hp': us.hp,
    'mana': us.mana,
    'attack': float(script.attack),
    'defence': float(script.defence),
    'resistance': float(script.resistance),
    'speed': float(script.speed),
    'luck': float(script.luck),
    'damage_specialization': script.damage_specialization,
    'action_ids': list(us.actions.values_list('id', flat=True)),
}

# enemy_scripts entry (per NPCScript):
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
```

`session['cooldowns']` is reset to `{}` at the top of the game view.

---

## Attack API Rewrite

`api/views.py` — full replacement:

```python
import time
import random
from django.http import JsonResponse
from script.models import Action
from script.combat import calculate_damage, effective_cast_time_ms, weighted_choice


def game_attack(request, source_id, target_id, attack_id, script_alignment):
    # 1. Resolve source and target from session
    if script_alignment == 'enemy':
        source = get_script_by_id(request.session.get('enemy_scripts', []), source_id)
        target_list = request.session.get('party_scripts', [])
    else:
        source = get_script_by_id(request.session.get('party_scripts', []), source_id)
        target_list = request.session.get('enemy_scripts', [])

    if not source:
        return JsonResponse({'error': 'Source not found'}, status=404)

    target = request.session.get('lowlife') if target_id == 0 \
        else get_script_by_id(target_list, target_id)

    if not target:
        return JsonResponse({'error': 'Target not found'}, status=404)

    # 2. Resolve available actions (respecting cooldowns)
    cooldowns = request.session.get('cooldowns', {})
    now = time.time()
    action_ids = source.get('action_ids', [])
    prefix = 'enemy' if script_alignment == 'enemy' else 'player'

    available = [
        aid for aid in action_ids
        if cooldowns.get(f'{prefix}:{source_id}:{aid}', 0) <= now
    ]

    if not available:
        # All on cooldown — find earliest expiry
        expiries = [cooldowns.get(f'{prefix}:{source_id}:{aid}', 0) for aid in action_ids]
        earliest = min(expiries) if expiries else now
        retry_ms = max(0, round((earliest - now) * 1000))
        return JsonResponse({
            'damage_done': 0, 'cast_time': 0, 'cool_down': 0,
            'action_name': None, 'is_crit': False,
            'type_multiplier': 1.0, 'retry_after_ms': retry_ms,
        })

    # 3. Weighted action selection
    if script_alignment == 'enemy':
        # Use pool weights from NPCScriptPoolEntry
        from script.models import NPCScriptPoolEntry
        entries = list(
            NPCScriptPoolEntry.objects
            .filter(npc_script_id=source_id, action_id__in=available)
            .values_list('action_id', 'weight')
        )
    else:
        # Player scripts: all assigned actions have equal weight (weights were
        # used at assignment time, not at attack time)
        entries = [(aid, 10) for aid in available]

    action_id = weighted_choice(entries) if entries else available[0]
    action = Action.objects.get(id=action_id)

    # 4. Compute damage
    damage, is_crit, type_mult = calculate_damage(action, source, target)

    # 5. Compute cast time with speed reduction
    cast_ms = effective_cast_time_ms(action, source.get('speed', 0))
    cool_ms = int(action.cooldown * 1000)

    # 6. Record cooldown
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
```

---

## Game Controller JS Changes

`processAttack` destructures the new response fields and updates the battle log:

```javascript
const { cast_time, cool_down, damage_done, action_name, is_crit, type_multiplier, retry_after_ms } = await res.json();

// Handle no-action (all on cooldown)
if (damage_done === 0 && action_name === null) {
    this.addLog(`${srcName} has no available actions`);
    src.setAttacking(false);
    // retry_after_ms tells us when to try again — game loop handles this naturally
    return;
}

// Build log message
let msg = `${srcName} used ${action_name} on ${tgtName} for ${damage_done} damage`;
if (is_crit) msg += ' — CRITICAL HIT!';
if (type_multiplier > 1.0) msg += ' (effective)';
if (type_multiplier < 1.0) msg += ' (glancing blow)';
if (tgt.isDead) msg += ' — FATAL!';
this.addLog(msg);
```

---

## `seed_actions` Management Command

Location: `script/management/commands/seed_actions.py`

Steps in order:
1. Fix `cast_time=0, is_instant=False` → set `is_instant=True` (bypass `full_clean` for this step using `update()`)
2. Fix `base_power=0` → random 5–20
3. Ensure each `Script` has ≥ 6 pool entries
4. Ensure each `NPCScript` has ≥ 1 pool entry
5. Backfill `UserScript.actions` for rows with 0 actions
6. Print summary

---

## Admin Changes

`script/admin.py`:

```python
@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_instant', 'base_power', 'cast_time', 'cooldown')
    list_editable = ('is_instant', 'base_power', 'cast_time', 'cooldown')
    list_filter = ('type', 'is_instant')
    fields = ('name', 'description', 'type', 'is_instant', 'cast_time',
              'base_power', 'cooldown', 'duration', 'max_targets', 'attribute_modified')

@admin.register(ScriptPoolEntry)
class ScriptPoolEntryAdmin(admin.ModelAdmin):
    list_display = ('script', 'action', 'weight')
    list_editable = ('weight',)

@admin.register(NPCScriptPoolEntry)
class NPCScriptPoolEntryAdmin(admin.ModelAdmin):
    list_display = ('npc_script', 'action', 'weight')
    list_editable = ('weight',)
```

---

## UI: Action Display Template Partial

`script/templates/script/_action_list.html` — reusable partial for both party page and script management page:

```html
{% load script_tags %}
{% if actions %}
<div class="mt-2 space-y-1">
    {% for action in actions %}
    <div class="flex items-center justify-between text-xs bg-base-200 rounded px-2 py-1">
        <span class="font-medium truncate">{{ action.name }}</span>
        <div class="flex gap-2 shrink-0 ml-2">
            <span class="badge badge-xs {{ action.type|type_color }}">{{ action.get_type_display }}</span>
            <span class="text-base-content/50">
                {% if action.is_instant %}Instant{% else %}{{ action.cast_time }}s{% endif %}
            </span>
            <span class="text-base-content/40">cd {{ action.cooldown }}s</span>
            <span class="text-warning font-bold">{{ action.base_power }}pw</span>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<p class="text-xs text-base-content/40 mt-2 italic">No actions assigned</p>
{% endif %}
```

The `type_color` template tag already exists in `script/templatetags/script_tags.py` and covers all action types.

---

## Files Changed

| File | Change |
|------|--------|
| `script/models.py` | Add `is_instant` to `Action`; add `ScriptPoolEntry`, `NPCScriptPoolEntry`; update `Script.action_pool` and `NPCScript.action_pool` to use through models; remove `action_pool` from `BaseScript` |
| `script/combat.py` | New file: `TYPE_MATCHUPS`, `weighted_choice()`, `calculate_damage()`, `effective_cast_time_ms()` |
| `script/admin.py` | Update `ActionAdmin`; add `ScriptPoolEntryAdmin`, `NPCScriptPoolEntryAdmin` |
| `script/management/commands/seed_actions.py` | New management command |
| `script/management/commands/populate_game_data.py` | Update to use `ScriptPoolEntry`/`NPCScriptPoolEntry` instead of `action_pool.add()` |
| `script/templates/script/_action_list.html` | New partial template |
| `script/templates/script/index.html` | Add action list to bench cards |
| `script/templates/script/index.html` | Add action list to party slot cards (via `get_party_state` update) |
| `users/models.py` | Add `assign_actions()` call in `UserScript.save()` on creation |
| `users/serializers.py` | Add `action_ids` to `UserScriptSerializer` |
| `game/views.py` | Reset `session['cooldowns']`; add stats + `action_ids` to session entries |
| `api/views.py` | Full rewrite using `script.combat` module |
| `game/static/js/game_controller.js` | Update `processAttack` to handle new response fields and log format |
| `users/migrations/` | Migration for `is_instant` on `Action` |
| `script/migrations/` | Migration for `ScriptPoolEntry`, `NPCScriptPoolEntry`, updated M2M fields |
