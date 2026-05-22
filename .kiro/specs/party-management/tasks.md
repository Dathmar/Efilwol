# Implementation Tasks: Party Management

## Tasks

- [ ] 1. Add `party_slot` field to `UserScript` model and migration
  - Add `party_slot = PositiveSmallIntegerField(null=True, blank=True)` to `UserScript`
  - Add `MELEE_SLOTS`, `RANGED_SLOTS`, `ALL_SLOTS` constants and `required_range_for_slot()` static method to `UserScript`
  - Update `save()` to keep `in_party` in sync: `in_party = party_slot is not None`
  - Generate and run migration
  - **Requirements:** 1.1, 1.2, 1.3

- [ ] 2. Update `UserScriptManager` with slot-aware methods
  - Add `assign_slot(user_script_id, slot, user_id)` — validates ownership, slot range, damage_range match, no duplicate slot; raises `ValueError` or `PermissionError`
  - Add `swap_slot(slot, user_script_id, user_id)` — wraps in `transaction.atomic()`, evicts current occupant to bench, assigns new script; returns `get_party_state()` result
  - Add `get_party_state(user_id)` — returns list of 5 dicts `{slot, user_script_id, name, role, damage_range}` with `None` values for empty slots
  - Add `repair_party(user)` — fixes missing/mismatched slots using bench first then global pool; returns count of repaired slots
  - Update `remove_from_party` to clear `party_slot` as well as `in_party`
  - Keep `add_to_party` working (delegate to `assign_slot` or keep as-is for bench→slot 1 fallback)
  - **Requirements:** 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5

- [ ] 3. Update `UserManager.create_user` for positional party assignment
  - Replace the `for _ in range(5): user.add_random_script(in_party=True)` loop
  - Select 3 distinct melee scripts and 2 distinct ranged scripts randomly
  - Raise `ValueError` if pool is insufficient, log the error
  - Create `UserScript` rows with `party_slot` 1–3 for melee, 4–5 for ranged, `in_party=True`
  - **Requirements:** 3.1, 3.2, 3.3, 3.4, 3.5

- [ ] 4. Add `repair_parties` management command
  - Create `users/management/commands/repair_parties.py`
  - Iterate all users; call `UserScript.objects.repair_party(user)` for each
  - Print per-user summary: slots repaired, scripts created
  - Handle the case where the global Script pool has no eligible scripts gracefully
  - **Requirements:** 4.1, 4.2, 4.3, 4.4, 4.5, 4.6

- [ ] 5. Add `POST /scripts/party/swap/` endpoint
  - Add `swap_party_slot(request)` view to `script/views.py`
  - Decorate with `@login_required` and `@require_POST`
  - Parse JSON body for `slot` and `user_script_id`
  - Delegate to `UserScript.objects.swap_slot()`; return JSON `{ok, party}` on success
  - Return 400 for invalid slot or wrong damage_range, 403 for wrong user
  - Add `path('party/swap/', views.swap_party_slot, name='swap-party-slot')` to `script/urls.py`
  - **Requirements:** 7.1, 7.2, 7.3, 7.4, 7.5, 7.6

- [ ] 6. Update `script/views.py` `index()` view
  - Run `UserScript.objects.repair_party(request.user)` silently on each visit
  - Pass `party_slots` (from `get_party_state()`) and `bench` (queryset of `party_slot=None` scripts) to template
  - Keep passing `user_scripts` for any remaining backward-compat usage
  - **Requirements:** 4.7, 5.5, 6.4

- [ ] 7. Rewrite `script/templates/script/index.html` — formation display
  - Wrap page in Alpine.js `x-data` with `selectedSlot`, `selectedSlotType`, `error`, `selectSlot()`, `swapScript()`
  - Render front row: 3 slot cards for slots 1–3 (melee), each clickable via `@click="selectSlot(n, 'melee')"`
  - Render back row: slot 4 card / Efilwol fixed card / slot 5 card
  - Slot card states: occupied (name + role badge + range badge), empty (placeholder), selected (ring highlight)
  - Efilwol card: distinct styling, no click handler, labeled "Fixed"
  - Expose `CSRF_TOKEN` in a `<script>` block for the fetch call
  - **Requirements:** 5.1, 5.2, 5.3, 5.4, 5.5

- [ ] 8. Rewrite `script/templates/script/index.html` — scrollable bench
  - Below the formation, render a scrollable section (fixed max-height, `overflow-y-auto`)
  - Each bench card shows: name, role badge, range badge, stats grid, type pill (reuse existing `type_color` tag)
  - Add `data-range="{{ us.script.damage_range }}"` attribute and `x-show` filter: hide when `selectedSlotType && script_range !== selectedSlotType`
  - Clicking a bench card calls `swapScript(userScriptId)` — disabled/greyed when no slot selected
  - Show `error` alert at top of bench section when `error` is set
  - **Requirements:** 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7

- [ ] 9. Update `game/views.py` to use `party_slot` ordering
  - Change party query from `filter(in_party=True)` to `filter(party_slot__isnull=False).order_by('party_slot')`
  - Ensure the game template still receives scripts in slot order (melee 1–3 first, then ranged 4–5)
  - Verify the lowlife insertion logic at `forloop.counter0 == 4` still works with ordered queryset

- [ ] 10. Write tests
  - `UserScriptManager.assign_slot`: valid, wrong user (403), invalid slot (400), wrong damage_range (400), duplicate slot (400)
  - `UserScriptManager.swap_slot`: success + round-trip, eviction to bench, atomic rollback on error
  - `UserScriptManager.repair_party`: missing melee slot, missing ranged slot, mismatched slot, already valid (no-op)
  - `UserManager.create_user`: 3 melee + 2 ranged assigned to correct slots, insufficient pool raises ValueError
  - `swap_party_slot` view: 200 success, 400 bad slot, 400 wrong range, 403 wrong user, 405 GET rejected
  - Party page renders: formation shows all 5 slots, Efilwol fixed, bench shows unassigned scripts
  - **Requirements:** all
