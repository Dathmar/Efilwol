# Implementation Plan: Script Attack System

## Overview

This plan implements the full script attack system overhaul: weighted action pool through models, `is_instant` validation, action assignment at UserScript creation, session-based cooldown tracking, a real damage formula with type matchups and crits, speed-based cast time reduction, updated UI pages, and comprehensive tests.

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1"] },
    { "wave": 2, "tasks": ["2"] },
    { "wave": 3, "tasks": ["3", "6"] },
    { "wave": 4, "tasks": ["4"] },
    { "wave": 5, "tasks": ["5", "7"] },
    { "wave": 6, "tasks": ["8", "9"] },
    { "wave": 7, "tasks": ["10"] }
  ]
}
```

## Notes

- Migrations must be generated and applied in order: Task 1 migration first, then Task 2 migration.
- The `seed_actions` command (Task 5) should be run after migrations to ensure data integrity.
- Task 10 (tests) should be written after all implementation tasks are complete.

## Tasks

- [x] 1. Add `is_instant` to `Action` model with validation
  - Add `is_instant = BooleanField(default=False)` to `Action`
  - Implement `Action.clean()` enforcing the bidirectional invariant: `is_instant=True → cast_time=0` and `cast_time=0 → is_instant=True`
  - Override `Action.save()` to call `self.full_clean()` before saving
  - Generate migration: add `is_instant` as nullable, data-migrate existing `cast_time=0` rows to `is_instant=True`, make non-nullable
  - Update `ActionAdmin` to show `is_instant` alongside `cast_time` with `list_editable` and correct `fields` ordering
  - **Requirements:** 7.1, 7.2, 7.3, 7.4, 7.5

- [x] 2. Add `ScriptPoolEntry` and `NPCScriptPoolEntry` through models
  - Add `ScriptPoolEntry(script FK, action FK, weight=10)` with `unique_together = ('script', 'action')`
  - Add `NPCScriptPoolEntry(npc_script FK, action FK, weight=10)` with `unique_together = ('npc_script', 'action')`
  - Remove `action_pool` from `BaseScript`
  - Add `action_pool = ManyToManyField(Action, through='ScriptPoolEntry', blank=True)` to `Script`
  - Add `action_pool = ManyToManyField(Action, through='NPCScriptPoolEntry', blank=True)` to `NPCScript`
  - Generate and run migration (data migration to copy existing `action_pool` rows into the new through tables)
  - Register `ScriptPoolEntryAdmin` and `NPCScriptPoolEntryAdmin` in `script/admin.py`
  - Update `populate_game_data` command to use `ScriptPoolEntry.objects.get_or_create()` instead of `action_pool.add()`
  - **Requirements:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.6

- [x] 3. Create `script/combat.py` — shared combat utilities
  - Implement `TYPE_MATCHUPS` dict with all 23 entries from the requirements
  - Implement `weighted_choice(entries)` — takes list of `(action_id, weight)` tuples, returns selected `action_id`
  - Implement `calculate_damage(action, attacker_dict, defender_dict)` — returns `(damage, is_crit, type_multiplier)`
    - Physical: mitigation = `defender['defence']`; non-physical: mitigation = `defender['resistance']`
    - `base_damage = max(1, base_power + attacker['attack'] - mitigation)`
    - `type_multiplier = TYPE_MATCHUPS.get((action.type, defender['damage_specialization']), 1.0)`
    - `crit_chance = attacker['luck'] / 100`; `crit_multiplier = 1.5 if random() < crit_chance else 1.0`
    - `final_damage = max(1, round(base_damage * type_multiplier * crit_multiplier))`
  - Implement `effective_cast_time_ms(action, attacker_speed)` — returns 0 for instant, else applies speed reduction
  - **Requirements:** 4.1–4.11

- [x] 4. Add `assign_actions()` to `UserScript` and call on creation
  - Add `assign_actions()` method to `UserScript` using `weighted_choice` from `script.combat`
  - Implement deduplication fallback: if weighted choices don't yield 6 unique, fill from remaining pool entries
  - Raise `ValueError` if pool has fewer than 6 entries
  - Override `UserScript.save()` to call `assign_actions()` after initial save (when `_state.adding` is True)
  - Update `UserScriptSerializer` to include `action_ids = serializers.SerializerMethodField()` returning `list(instance.actions.values_list('id', flat=True))`
  - **Requirements:** 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7

- [x] 5. Create `seed_actions` management command
  - Step 1: `Action.objects.filter(cast_time=0, is_instant=False).update(is_instant=True)` (bypass `full_clean` via `update()`)
  - Step 2: For each `Action` with `base_power=0`, set to `random.randint(5, 20)` and save (using `update()` to bypass validation)
  - Step 3: For each `Script` with fewer than 6 pool entries, add random `Action` records from the global pool via `ScriptPoolEntry`
  - Step 4: For each `NPCScript` with 0 pool entries, add at least one `Action` via `NPCScriptPoolEntry`
  - Step 5: For each `UserScript` with `actions.count() == 0`, call `us.assign_actions()`
  - Print per-entity-type summary; ensure idempotency (use `get_or_create` for pool entries)
  - **Requirements:** 10.1–10.10

- [x] 6. Update `game/views.py` — session structure
  - Reset `session['cooldowns'] = {}` at the top of the `game()` view before any other session writes
  - Extend `party_session` entries to include: `attack`, `defence`, `resistance`, `speed`, `luck`, `damage_specialization`, `action_ids`
  - Extend `enemy_session` entries to include: `attack`, `defence`, `resistance`, `speed`, `luck`, `damage_specialization`, `action_ids` (from `npc.pool_entries.values_list('action_id', flat=True)`)
  - For demo party (anon users), include `action_ids: []` as a placeholder (no actions assigned to demo scripts)
  - **Requirements:** 3.1, 9.1, 9.2

- [x] 7. Rewrite `api/views.py` — real attack calculation
  - Import and use `calculate_damage`, `effective_cast_time_ms`, `weighted_choice` from `script.combat`
  - Resolve available actions from `source['action_ids']` filtered by `Cooldown_Store`
  - For enemy sources: use `NPCScriptPoolEntry` weights for weighted selection
  - For player sources: use equal weights (10 each) — weights were applied at assignment time
  - Handle no-action case: return `retry_after_ms` = ms until earliest cooldown expires
  - Write cooldown to `session['cooldowns']` and set `session.modified = True`
  - Return full response: `damage_done`, `cast_time`, `cool_down`, `action_name`, `is_crit`, `type_multiplier`, `retry_after_ms`
  - Fall back to DB lookup if `action_ids` missing from session (log warning)
  - **Requirements:** 3.2–3.8, 4.12–4.15, 5.1–5.6, 9.3, 9.4

- [x] 8. Update `game_controller.js` — handle new API response
  - Destructure `action_name`, `is_crit`, `type_multiplier`, `retry_after_ms` from attack response
  - Handle no-action response (`damage_done === 0 && action_name === null`): log `"{name} has no available actions"`, skip damage application
  - Build enriched log message: base format + CRITICAL HIT suffix + effective/glancing blow suffix + FATAL suffix
  - No changes needed to animation logic — `cast_time` and `cool_down` are still returned in ms
  - **Requirements:** 6.1–6.7

- [x] 9. Add `_action_list.html` partial and wire into party and script pages
  - Create `script/templates/script/_action_list.html` showing name, type badge (using `type_color` tag), cast time (Instant or Xs), cooldown, base_power
  - Update `script/views.py` `index()` to prefetch `actions` on bench queryset: `.prefetch_related('actions')`
  - Update `get_party_state()` in `users/managers.py` to include `actions` data (list of dicts with name, type, is_instant, cast_time, cooldown, base_power) — or pass `UserScript` objects with prefetched actions
  - Include `_action_list.html` in `_script_card_body.html` (bench cards) and in the party slot section of `index.html`
  - **Requirements:** 8.1–8.4, 11.1–11.4, 12.1–12.4

- [x] 10. Write tests
  - `Action` validation: `is_instant=True, cast_time=1.0` raises `ValidationError`; `cast_time=0, is_instant=False` raises `ValidationError`; valid combinations save cleanly
  - `weighted_choice`: statistical test — weight 30 vs weight 10 over 1000 draws yields ≥ 2:1 ratio
  - `calculate_damage`: physical uses defence, non-physical uses resistance; type multiplier applied correctly for 3 matchup cases; `luck=0` never crits; `luck=100` always crits; minimum damage is 1
  - `effective_cast_time_ms`: instant action returns 0; speed=0 returns raw ms; speed=10 returns 80% of raw ms; speed=50 capped at 80%
  - `UserScript.assign_actions`: exactly 6 unique actions assigned; raises `ValueError` if pool < 6; weighted distribution property
  - `game_attack` view: returns `action_name`, `is_crit`, `type_multiplier`; cooldown written to session; no-action response when all on cooldown includes `retry_after_ms`; session reset on game view load
  - **Requirements:** all
