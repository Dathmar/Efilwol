# Requirements Document

## Introduction

The script attack system overhaul replaces the placeholder combat logic in the Efilwol RPG game with a fully data-driven attack pipeline. Currently the attack API returns random damage and cast times, ignoring all model data. This feature introduces weighted action pool through models, automatic action assignment to UserScripts at creation time, session-based cooldown tracking for both players and NPCs, a real damage formula with type matchups, critical hits, and speed-based cast time reduction, and updated UI pages that display each script's assigned actions.

---

## Glossary

- **Action**: A combat move defined by the `Action` model, with fields `name`, `description`, `base_power`, `type`, `cast_time`, `is_instant`, `cooldown`, `duration`, `max_targets`, and `attribute_modified`.
- **Action_Pool**: The set of `Action` records available to a given `Script` or `NPCScript`, stored via the appropriate pool through model.
- **ScriptPoolEntry**: The through model for `Script → Action` pool entries. Adds a `weight` field.
- **NPCScriptPoolEntry**: The through model for `NPCScript → Action` pool entries. Adds a `weight` field.
- **Weight**: A `PositiveIntegerField` on pool entries (default 10). Higher weight = higher probability of selection.
- **Assigned_Actions**: The 6 `Action` records drawn from a `Script`'s pool and stored on a `UserScript` at creation time. Fixed after assignment.
- **UserScript**: The join model linking a `User` to a `Script`, with an `actions` ManyToManyField holding the Assigned_Actions.
- **Cooldown_Store**: `session['cooldowns']` — a dict mapping `'player:{id}:{action_id}'` or `'enemy:{id}:{action_id}'` to a Unix expiry timestamp (float seconds since epoch).
- **Attack_API**: The endpoint at `/api/v1/game/attack/<source_id>/<target_id>/<attack_id>/<script_alignment>/`.
- **Script_Alignment**: The `script_alignment` URL parameter — `'player'` or `'enemy'`.
- **Type_Matchup**: A multiplier applied to damage based on the action's `type` and the defender's `damage_specialization`. See Requirement 4.
- **Critical_Hit**: A random bonus triggered by the attacker's `luck` stat. Multiplies final damage by 1.5.
- **Instant_Action**: An `Action` with `is_instant = True`. `cast_time` must be 0. Displayed as "Instant" in all UI contexts.
- **Cast_Time_Ms**: `int(action.cast_time * 1000)`.
- **Cooldown_Ms**: `int(action.cooldown * 1000)`.
- **Effective_Cast_Time_Ms**: Cast time after speed reduction: `round(Cast_Time_Ms * (1 - min(0.20, attacker.speed / 50)))`.
- **Party_Page**: The scripts/party UI page.
- **Script_Management_Page**: The script management UI page.
- **NPC**: A non-player combatant (`NPCScript`). Uses full Action_Pool, not a fixed 6.
- **HoT/DoT**: Heal-over-time / damage-over-time. Governed by `Action.duration`. Reserved for future implementation; all existing actions have `duration = null`.

---

## Requirements

### Requirement 1: Action Pool Through Models

**User Story:** As a game designer, I want to assign a weight to each action in a script's pool, so that some actions are more likely to be selected when a UserScript is created or when an NPC attacks.

#### Acceptance Criteria

1. THE `ScriptPoolEntry` model SHALL be the through model for `Script.action_pool`, with fields: `script (FK → Script)`, `action (FK → Action)`, `weight (PositiveIntegerField, default=10)`.
2. THE `NPCScriptPoolEntry` model SHALL be the through model for `NPCScript.action_pool`, with fields: `npc_script (FK → NPCScript)`, `action (FK → Action)`, `weight (PositiveIntegerField, default=10)`.
3. WHEN a pool entry is created without specifying a weight, THE system SHALL store a weight of 10.
4. EACH through model SHALL enforce a unique constraint on `(script/npc_script, action)` — no duplicate action entries per script pool.
5. FOR ALL weighted draws over a pool where one action has weight 30 and another has weight 10, THE weighted selection algorithm SHALL select the higher-weight action at a ratio of at least 2:1 over 1000 draws (statistical property).
6. THE `action_pool` ManyToManyField on `BaseScript` SHALL be replaced by the appropriate through model on `Script` and `NPCScript` respectively.

---

### Requirement 2: UserScript Action Assignment at Creation

**User Story:** As a player, I want my script to automatically receive 6 actions when it is assigned to me, so that it is ready for combat without any manual setup.

#### Acceptance Criteria

1. WHEN a `UserScript` is created, THE system SHALL draw exactly 6 unique `Action` records from the associated `Script`'s pool using weighted random selection and store them in `UserScript.actions`.
2. THE `UserScript.actions` set SHALL contain no duplicate `Action` records.
3. WHEN the associated `Script`'s pool contains fewer than 6 actions, THE system SHALL raise a `ValueError` with a descriptive message and prevent the `UserScript` from being saved.
4. THE Assigned_Actions SHALL be fixed at creation time and SHALL NOT change unless explicitly reassigned by an administrative operation.
5. FOR ALL `UserScript` records created from a pool of ≥ 6 actions, `UserScript.actions.count()` SHALL equal exactly 6.
6. FOR ALL `UserScript` records, the set of action IDs in `UserScript.actions` SHALL contain no repeated values.
7. FOR ALL pools where action A has a higher weight than action B, action A SHALL appear in `UserScript.actions` more frequently than action B across many creations from the same pool (weighted distribution property).

---

### Requirement 3: Session Initialisation and Cooldown Tracking

**User Story:** As a player, I want each battle to start with a clean slate and track which actions are on cooldown during combat, so that cooldowns from previous battles do not carry over.

#### Acceptance Criteria

1. WHEN the game view is loaded (a new battle session begins), THE game view SHALL reset `session['cooldowns']` to `{}` before storing any other session data.
2. THE `Cooldown_Store` SHALL be stored in the Django session under the key `'cooldowns'` as a dict mapping cooldown keys to Unix expiry timestamps.
3. WHEN an action is used by a player combatant with id `{id}` and action id `{action_id}`, THE `Attack_API` SHALL write `'player:{id}:{action_id}'` → `time.time() + float(action.cooldown)` into the `Cooldown_Store`.
4. WHEN an action is used by an enemy combatant, THE `Attack_API` SHALL write `'enemy:{id}:{action_id}'` → `time.time() + float(action.cooldown)` into the `Cooldown_Store`.
5. WHEN the `Attack_API` selects an action, THE system SHALL exclude any action whose cooldown key has an expiry timestamp greater than `time.time()`.
6. WHEN a cooldown key has an expiry timestamp ≤ `time.time()`, THE system SHALL treat that action as available.
7. IF all actions for a combatant are on cooldown, THE `Attack_API` SHALL return HTTP 200 with `damage_done=0`, `cast_time=0`, `cool_down=0`, `action_name=null`, `is_crit=false`, `type_multiplier=1.0`, `retry_after_ms` set to the number of milliseconds until the earliest cooldown expires.
8. FOR ALL combatants, an action with a future expiry in the `Cooldown_Store` SHALL never be returned as the selected action.

---

### Requirement 4: Damage Formula with Type Matchups, Crits, and Speed

**User Story:** As a player, I want attacks to deal damage that reflects the attacker's stats, the action's power, elemental matchups, speed, and the chance of a critical hit, so that combat is strategic and varied.

#### Acceptance Criteria

**Base damage:**
1. THE `Attack_API` SHALL compute base damage as:
   `base_damage = max(1, base_power + attacker.attack - mitigation)`
   where `mitigation = defender.defence` if `action.type == 'physical'`, else `mitigation = defender.resistance`.

**Type matchup:**
2. THE `Attack_API` SHALL apply a `type_multiplier` from the Type_Matchup table based on `(action.type, defender.damage_specialization)`. If no entry exists, `type_multiplier = 1.0`.
3. THE Type_Matchup table SHALL be:

   | Attack type  | Defender specialization | Multiplier |
   |-------------|------------------------|------------|
   | fire        | ice                    | 2.0        |
   | fire        | fire                   | 0.5        |
   | fire        | water                  | 0.5        |
   | ice         | fire                   | 2.0        |
   | ice         | ice                    | 0.5        |
   | ice         | earth                  | 1.5        |
   | lightning   | water                  | 2.0        |
   | lightning   | earth                  | 0.5        |
   | lightning   | lightning              | 0.5        |
   | water       | fire                   | 1.5        |
   | water       | lightning              | 0.5        |
   | water       | water                  | 0.5        |
   | earth       | lightning              | 1.5        |
   | earth       | earth                  | 0.5        |
   | poison      | earth                  | 1.5        |
   | poison      | poison                 | 0.5        |
   | holy        | dark                   | 2.0        |
   | holy        | necrotic               | 2.0        |
   | holy        | holy                   | 0.5        |
   | dark        | holy                   | 2.0        |
   | dark        | dark                   | 0.5        |
   | necrotic    | holy                   | 1.5        |
   | physical    | physical               | 1.0        |

**Critical hit:**
4. THE `Attack_API` SHALL compute `crit_chance = attacker.luck / 100`. A random float in [0, 1) less than `crit_chance` triggers a critical hit.
5. WHEN a critical hit occurs, `crit_multiplier = 1.5`. When no critical hit occurs, `crit_multiplier = 1.0`.
6. A script with `luck = 0` SHALL have a 0% critical hit chance and SHALL never trigger a critical hit.

**Speed-based cast time reduction:**
7. THE `Attack_API` SHALL compute the Effective_Cast_Time_Ms as:
   `effective_cast_time_ms = round(Cast_Time_Ms * (1 - min(0.20, attacker.speed / 50)))`
   Maximum reduction is 20%, reached at `speed = 10`.
8. THE `cast_time` field in the API response SHALL be the Effective_Cast_Time_Ms, not the raw Cast_Time_Ms.
9. WHEN `is_instant = True`, speed reduction SHALL NOT be applied; `effective_cast_time_ms` SHALL remain 0.

**Final damage:**
10. THE final damage SHALL be: `final_damage = max(1, round(base_damage * type_multiplier * crit_multiplier))`.
11. FOR ALL valid stat combinations, `final_damage` SHALL be ≥ 1.

**API response:**
12. THE `Attack_API` SHALL return a JSON response containing:
    - `damage_done` (int)
    - `cast_time` (Effective_Cast_Time_Ms int)
    - `cool_down` (Cooldown_Ms int)
    - `action_name` (string or null)
    - `is_crit` (bool)
    - `type_multiplier` (float)
    - `retry_after_ms` (int, 0 when an action was taken)
13. FOR ALL selected actions, `cool_down` in the response SHALL equal `int(action.cooldown * 1000)`.
14. IF the source combatant is not found in the session, THE `Attack_API` SHALL return HTTP 404.
15. IF the target combatant is not found in the session, THE `Attack_API` SHALL return HTTP 404.

---

### Requirement 5: NPC Action Selection

**User Story:** As a game designer, I want NPCs to select actions from their full action pool during combat, respecting cooldowns and weights.

#### Acceptance Criteria

1. WHEN an NPC attacks, THE `Attack_API` SHALL select an action from the NPC's full Action_Pool, not a fixed 6.
2. WHEN an NPC attacks, THE `Attack_API` SHALL exclude actions on cooldown under `'enemy:{id}:{action_id}'`.
3. WHEN multiple actions are available, THE `Attack_API` SHALL select using weighted random selection based on `NPCScriptPoolEntry.weight`.
4. WHEN exactly one action is available, THE `Attack_API` SHALL select it.
5. IF all NPC actions are on cooldown, THE `Attack_API` SHALL return the no-action response from Requirement 3, criterion 7.
6. FOR ALL NPC attack responses with a selected action, `action_name` SHALL match the `name` of an `Action` in the NPC's Action_Pool.

---

### Requirement 6: Battle Log — Action Name and Combat Events

**User Story:** As a player, I want the battle log to show the action used, whether it was a critical hit, and whether it was effective or resisted.

#### Acceptance Criteria

1. THE `Attack_API` SHALL include `action_name`, `is_crit`, and `type_multiplier` in every attack response.
2. WHEN the battle log displays a normal attack, THE game controller SHALL render: `"{attacker} used {action_name} on {target} for {damage} damage"`.
3. WHEN `is_crit` is true, THE game controller SHALL append `"— CRITICAL HIT!"` to the log message.
4. WHEN `type_multiplier > 1.0`, THE game controller SHALL append `"(effective)"` to the log message.
5. WHEN `type_multiplier < 1.0`, THE game controller SHALL append `"(glancing blow)"` to the log message.
6. WHEN no action is taken (all on cooldown), THE game controller SHALL log `"{attacker} has no available actions"`.
7. `action_name` SHALL be a non-empty string when an action is selected, or `null` when no action is taken.

---

### Requirement 7: `Action.is_instant` Field and Validation

**User Story:** As a game designer, I want a clear, explicit flag on actions that fire instantly, so that zero cast time is always intentional and never accidental.

#### Acceptance Criteria

1. THE `Action` model SHALL include an `is_instant` field of type `BooleanField` with a default of `False`.
2. WHEN `Action.is_instant = True`, THE model's `clean()` method SHALL enforce that `cast_time = 0`. If `cast_time != 0` and `is_instant = True`, a `ValidationError` SHALL be raised: "Instant actions must have cast_time = 0."
3. WHEN `Action.cast_time = 0` and `is_instant = False`, THE model's `clean()` method SHALL raise a `ValidationError`: "cast_time can only be 0 if is_instant is True."
4. THE `Action.save()` method SHALL call `full_clean()` to enforce these constraints on every save, not only through form validation.
5. THE Django admin for `Action` SHALL display `is_instant` as an editable field alongside `cast_time`, so that designers cannot set one without seeing the other.
6. FOR ALL existing `Action` records with `cast_time = 0` after migration, THE `seed_actions` command SHALL set `is_instant = True` on those records before any other validation runs.
7. FOR ALL `Action` records in the database after `seed_actions` completes, the invariant `(is_instant = True ↔ cast_time = 0)` SHALL hold for every record.

---

### Requirement 8: Instant Action Display

**User Story:** As a player, I want actions with no cast time to be clearly labelled as "Instant" in the UI.

#### Acceptance Criteria

1. WHEN an `Action` has `is_instant = True`, ALL UI contexts that display cast time SHALL render "Instant".
2. This applies to: the Party_Page action list, the Script_Management_Page action list, and any future action display contexts.
3. WHEN an `Action` has `is_instant = False` and `cast_time > 0`, THE UI SHALL display the value in seconds (e.g. "1.5s").

---

### Requirement 9: Session Action Data

**User Story:** As a developer, I want the game session to include each combatant's assigned action IDs, so that the Attack API can resolve actions without additional database queries per request.

#### Acceptance Criteria

1. WHEN the game view builds `session['party_scripts']`, EACH party script entry SHALL include an `action_ids` list containing the IDs of the `UserScript`'s Assigned_Actions.
2. WHEN the game view builds `session['enemy_scripts']`, EACH enemy entry SHALL include an `action_ids` list containing the IDs of all `Action` records in the NPC's Action_Pool.
3. THE `Attack_API` SHALL resolve available actions for a combatant using the `action_ids` from the session, then fetch action details from the database in a single query (`Action.objects.filter(id__in=action_ids)`).
4. IF `action_ids` is missing from a session entry, THE `Attack_API` SHALL fall back to a database lookup and log a warning.

---

### Requirement 10: Data Integrity Management Command

**User Story:** As a developer, I want a management command that ensures all scripts, NPCs, and UserScripts have valid action data, so that the game can run correctly after deployment.

#### Acceptance Criteria

1. THE system SHALL provide a management command named `seed_actions` that performs all of the following in a single run.
2. FOR EACH `Action` with `cast_time = 0` and `is_instant = False`, THE command SHALL set `is_instant = True` (fixing legacy records before validation is enforced).
3. FOR EACH `Action` with `base_power = 0`, THE command SHALL update `base_power` to a random integer between 5 and 20 (inclusive).
4. FOR EACH `Action` with `cast_time = 0` and `is_instant = False` that was NOT fixed by criterion 2 (i.e. a record that somehow still violates the invariant), THE command SHALL report it as an error.
5. FOR EACH `Action` with `cast_time > 0` that should be instant (detected by `is_instant = True`), THE command SHALL set `cast_time = 0`.
6. FOR EACH `Script` with fewer than 6 actions in its pool, THE command SHALL add randomly selected `Action` records from the global `Action` table until the pool has at least 6 entries, using default weight 10.
7. FOR EACH `NPCScript` with an empty Action_Pool, THE command SHALL add at least one `Action` to its pool.
8. FOR EACH `UserScript` with `UserScript.actions.count() = 0`, THE command SHALL assign 6 actions from the associated `Script`'s pool using weighted random selection.
9. THE command SHALL be idempotent — running it multiple times SHALL NOT create duplicate pool entries or duplicate assigned actions.
10. THE command SHALL print a per-entity-type summary of all changes made.

---

### Requirement 11: HoT/DoT Architecture (Reserved)

**User Story:** As a game designer, I want the action model to support heal-over-time and damage-over-time effects in the future, without requiring a model change when that feature is built.

#### Acceptance Criteria

1. THE `Action.duration` field SHALL remain on the model as a nullable integer (seconds).
2. ALL existing `Action` records SHALL have `duration = null`, indicating no HoT/DoT effect.
3. THE `Attack_API` SHALL ignore `duration` for all actions where `duration` is null.
4. THE `Attack_API` SHALL NOT implement HoT/DoT processing in this feature — that is deferred to a future spec.
5. THE data model SHALL support a future `duration > 0` meaning "apply `base_power` damage/healing per second for `duration` seconds" without requiring a migration.

---

### Requirement 12: Party Page — Assigned Action Display

**User Story:** As a player, I want to see the 6 actions assigned to each of my party members, so that I can plan my combat strategy.

#### Acceptance Criteria

1. THE `Party_Page` SHALL display each party member's Assigned_Actions showing `name`, `type`, `cast_time` (formatted per Requirement 8), `cooldown` (in seconds), and `base_power`.
2. THE display SHALL be read-only.
3. WHEN a `UserScript` has no Assigned_Actions, THE `Party_Page` SHALL display "No actions assigned".
4. THE `Party_Page` SHALL prefetch actions to avoid N+1 queries.

---

### Requirement 13: Script Management Page — Assigned Action Display

**User Story:** As a player, I want to see the actions assigned to each of my scripts on the management page, so that I can review each script's capabilities.

#### Acceptance Criteria

1. THE `Script_Management_Page` SHALL display each script's Assigned_Actions showing `name`, `type`, `cast_time` (formatted per Requirement 8), `cooldown` (in seconds), and `base_power`.
2. THE display SHALL be read-only.
3. WHEN a script has no Assigned_Actions, THE `Script_Management_Page` SHALL display "No actions assigned".
4. THE `Script_Management_Page` SHALL prefetch actions to avoid N+1 queries.
