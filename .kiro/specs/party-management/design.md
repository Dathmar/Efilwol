# Design Document: Party Management

## Overview

This feature replaces the flat scripts page with a positional party formation system. The core change is adding a `party_slot` field to `UserScript` that encodes both party membership and position. All composition enforcement lives in `UserScriptManager`. The UI uses Alpine.js for slot selection state and HTMX to POST swaps without a full page reload.

---

## Data Model Changes

### `UserScript.party_slot`

Add a nullable `PositiveSmallIntegerField` to `UserScript`:

```python
party_slot = models.PositiveSmallIntegerField(
    null=True, blank=True,
    help_text="Party position 1-5, or null if on bench. Slots 1-3=melee, 4-5=ranged."
)
```

**Constraints (enforced at the manager level, not DB-level):**
- Values must be in `{1, 2, 3, 4, 5}` or `None`
- Unique per user — no two `UserScript` rows for the same user may share the same non-null `party_slot`
- Slots 1–3 require `script.damage_range == 'melee'`
- Slots 4–5 require `script.damage_range == 'ranged'`

**`in_party` field:** Keep as a real DB field (not a property) because it is used in `filter()` queries throughout the codebase. Update it automatically whenever `party_slot` changes — set `in_party=True` when `party_slot` is assigned, `in_party=False` when cleared. This preserves all existing query compatibility.

**Migration:** Add `party_slot` as nullable. Existing rows keep `party_slot=None`. The `repair_parties` command backfills slots for existing users.

### Slot type constants

Add to `UserScript` (or a shared constants module):

```python
MELEE_SLOTS = frozenset({1, 2, 3})
RANGED_SLOTS = frozenset({4, 5})
ALL_SLOTS = MELEE_SLOTS | RANGED_SLOTS

@staticmethod
def required_range_for_slot(slot: int) -> str:
    if slot in MELEE_SLOTS: return 'melee'
    if slot in RANGED_SLOTS: return 'ranged'
    raise ValueError(f"Invalid slot {slot}")
```

---

## Manager Changes: `UserScriptManager`

### New methods

```python
def assign_slot(self, user_script_id: int, slot: int, user_id: int) -> UserScript:
    """
    Assign a bench script to a party slot.
    Raises ValueError if: wrong user, invalid slot, wrong damage_range,
    or slot already occupied.
    """

def swap_slot(self, slot: int, user_script_id: int, user_id: int) -> dict:
    """
    Atomically swap a bench script into a slot, moving the current occupant
    to the bench. Returns updated party state dict.
    Wraps everything in transaction.atomic().
    """

def get_party_state(self, user_id: int) -> list[dict]:
    """
    Return list of 5 dicts, one per slot, with keys:
    slot, script_name, role, damage_range, user_script_id (or None if empty).
    """

def repair_party(self, user) -> int:
    """
    Inspect user's party, fill missing/mismatched slots.
    Returns count of slots repaired.
    """
```

### Updated methods

- `add_to_party` — deprecated in favour of `assign_slot`; keep for backward compat but delegate internally
- `remove_from_party` — clears `party_slot` and sets `in_party=False`
- `MAX_PARTY_SIZE` — remains 5

---

## `UserManager.create_user` Changes

Replace the current loop of 5 random scripts with:

```python
melee_scripts = Script.objects.filter(damage_range='melee').order_by('?')[:3]
ranged_scripts = Script.objects.filter(damage_range='ranged').order_by('?')[:2]

if len(melee_scripts) < 3 or len(ranged_scripts) < 2:
    raise ValueError("Not enough scripts in pool to create a valid starting party.")

for slot, script in zip([1, 2, 3], melee_scripts):
    UserScript.objects.create(user=user, script=script, party_slot=slot, in_party=True, hp=script.hp)

for slot, script in zip([4, 5], ranged_scripts):
    UserScript.objects.create(user=user, script=script, party_slot=slot, in_party=True, hp=script.hp)
```

---

## New Management Command: `repair_parties`

Location: `users/management/commands/repair_parties.py`

Algorithm per user:
1. Load all `UserScript` rows for the user
2. Find occupied melee slots (party_slot in {1,2,3}) and ranged slots (party_slot in {4,5})
3. Find mismatched slots (e.g. a ranged script in slot 1) — move to bench
4. For each empty slot, try bench scripts of the right type first; if none, create a new `UserScript` from the global `Script` pool
5. Log changes per user

---

## New API Endpoint: `POST /scripts/party/swap/`

Location: `script/views.py` (new view) + `script/urls.py`

**Request body (JSON or form):**
```
slot: int (1-5)
user_script_id: int
```

**Response (JSON):**
```json
{
  "ok": true,
  "party": [
    {"slot": 1, "user_script_id": 12, "name": "Knight", "role": "tank", "damage_range": "melee"},
    ...
  ]
}
```

**Error responses:**
- 400: invalid slot, wrong damage_range
- 403: script doesn't belong to user
- 405: non-POST

**Implementation:**
```python
@login_required
@require_POST
def swap_party_slot(request):
    data = json.loads(request.body)
    slot = int(data['slot'])
    user_script_id = int(data['user_script_id'])
    try:
        party = UserScript.objects.swap_slot(slot, user_script_id, request.user.id)
        return JsonResponse({'ok': True, 'party': party})
    except PermissionError:
        return JsonResponse({'ok': False, 'error': '...'}, status=403)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
```

---

## Party Page UI

### URL and view

Keep the existing route `scripts/` → `script:index`. The view passes:

```python
{
    'party_slots': party_slots,   # list of 5 dicts from get_party_state()
    'bench': bench_scripts,       # UserScript queryset with party_slot=None
    'user_scripts': all_scripts,  # for backward compat if needed
}
```

### Layout

```
┌─────────────────────────────────────────────────────┐
│  FRONT ROW (melee)                                  │
│  [Slot 1]  [Slot 2]  [Slot 3]                       │
├─────────────────────────────────────────────────────┤
│  BACK ROW                                           │
│  [Slot 4]  [Efilwol★]  [Slot 5]                    │
└─────────────────────────────────────────────────────┘
│  YOUR SCRIPTS  (scrollable, filtered when slot selected)
│  [Card] [Card] [Card] [Card] ...                    │
└─────────────────────────────────────────────────────┘
```

### Alpine.js state

The page wrapper uses `x-data`:

```javascript
{
    selectedSlot: null,       // int 1-5 or null
    selectedSlotType: null,   // 'melee' or 'ranged'
    error: null,

    selectSlot(slot, type) {
        this.selectedSlot = (this.selectedSlot === slot) ? null : slot;
        this.selectedSlotType = this.selectedSlot ? type : null;
    },

    async swapScript(userScriptId) {
        if (!this.selectedSlot) return;
        const res = await fetch('/scripts/party/swap/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN},
            body: JSON.stringify({slot: this.selectedSlot, user_script_id: userScriptId})
        });
        const data = await res.json();
        if (data.ok) {
            window.location.reload();  // simplest correct approach
        } else {
            this.error = data.error;
        }
    }
}
```

### Bench filtering

Each bench card has `x-show`:

```html
<div x-show="!selectedSlotType || script_range === selectedSlotType">
```

The `script_range` value is rendered server-side as a data attribute on each card.

### Slot card states

- **Occupied + not selected:** shows name, role badge, range badge
- **Occupied + selected:** highlighted ring, "click bench script to swap"
- **Empty + not selected:** placeholder with slot type label
- **Empty + selected:** highlighted ring, "select a script below"
- **Efilwol:** always shows fixed card, no click handler, distinct styling

---

## Login-time Party Repair

In `script/views.py` `index()`:

```python
if request.user.is_authenticated:
    repaired = UserScript.objects.repair_party(request.user)
    if repaired:
        logger.info(f"Repaired {repaired} party slots for {request.user.email}")
```

This runs silently on every visit to the party page. It's cheap (5 DB rows max per user) and ensures the page never renders a broken formation.

---

## Files Changed

| File | Change |
|------|--------|
| `users/models.py` | Add `party_slot` field to `UserScript`; update `in_party` sync logic |
| `users/managers.py` | Add `assign_slot`, `swap_slot`, `get_party_state`, `repair_party`; update `create_user` |
| `users/migrations/` | New migration for `party_slot` field |
| `users/management/commands/repair_parties.py` | New management command |
| `script/views.py` | Update `index()` to pass `party_slots` + `bench`; add `swap_party_slot` view |
| `script/urls.py` | Add `party/swap/` route |
| `script/templates/script/index.html` | Full rewrite with formation + scrollable bench |
| `game/views.py` | Update party query to use `party_slot` ordering |
| `game/tests.py` | Update tests for new party structure |

---

## Test Coverage

- `UserScriptManager.assign_slot` — valid assignment, wrong user, invalid slot, wrong damage_range, duplicate slot
- `UserScriptManager.swap_slot` — atomic swap, eviction to bench, round-trip property
- `UserScriptManager.repair_party` — missing slots, mismatched slots, already valid
- `UserManager.create_user` — correct 3+2 assignment, insufficient pool error
- `swap_party_slot` view — 200 success, 400 bad slot, 400 wrong range, 403 wrong user, 405 GET
- Party page — formation renders, bench filters, Efilwol fixed
