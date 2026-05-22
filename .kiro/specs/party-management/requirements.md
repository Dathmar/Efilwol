# Requirements Document

## Introduction

The party management feature replaces the current flat scripts page with a positional party formation system for the Efilwol RPG game. A valid party consists of exactly 3 melee scripts in front-row slots (slots 1–3), Efilwol (the lowlife) fixed in the center-back position, and exactly 2 ranged scripts in back-row slots (slots 4–5). The feature covers the data model changes needed to track slot positions, a new interactive party management UI, automatic party assignment on account creation, and a repair mechanism for existing accounts whose parties do not meet the composition rules.

---

## Glossary

- **Party**: The set of 5 active scripts assigned to a user for combat, arranged in a fixed formation.
- **Party_Slot**: A numbered positional slot (1–5) within a party. Slots 1–3 are melee (front row); slots 4–5 are ranged (back row).
- **Melee_Slot**: A Party_Slot with position 1, 2, or 3, which only accepts scripts with `damage_range='melee'`.
- **Ranged_Slot**: A Party_Slot with position 4 or 5, which only accepts scripts with `damage_range='ranged'`.
- **Efilwol**: The fixed lowlife NPC occupying the center-back position of every party. Efilwol is not a Script and cannot be swapped.
- **Script**: A player-owned combat unit defined by the `Script` model, with a `damage_range` of either `melee` or `ranged`.
- **UserScript**: The join model linking a `User` to a `Script`, extended with a `party_slot` field to record positional assignment.
- **Bench**: The collection of scripts a user owns that are not currently assigned to any Party_Slot (`party_slot=None`).
- **Party_Manager**: The server-side component responsible for enforcing party composition rules.
- **Party_Page**: The UI page that replaces the current scripts page, showing the formation and the bench.
- **Formation_Display**: The top section of the Party_Page showing the 5 positional slots and Efilwol.
- **Bench_List**: The scrollable bottom section of the Party_Page showing scripts not in the party.
- **Selected_Slot**: The Party_Slot currently highlighted by the user for a swap interaction.
- **Eligible_Script**: A script on the bench whose `damage_range` matches the type required by the Selected_Slot.

---

## Requirements

### Requirement 1: Positional Party Slot Model

**User Story:** As a developer, I want each UserScript to record which party slot it occupies, so that the system can enforce positional composition rules and render the formation correctly.

#### Acceptance Criteria

1. THE `UserScript` model SHALL include a `party_slot` field that stores an integer value of 1, 2, 3, 4, or 5, or `null` when the script is on the bench.
2. WHEN a `UserScript` is assigned to a Party_Slot, THE `UserScript` model SHALL enforce that `party_slot` is unique per user (no two UserScripts for the same user may share the same `party_slot` value).
3. THE `UserScript` model SHALL derive `in_party` as `True` if and only if `party_slot` is not `null`, maintaining backward compatibility with existing code that reads `in_party`.
4. WHEN a `UserScript` is assigned to a Melee_Slot (party_slot ∈ {1, 2, 3}), THE `Party_Manager` SHALL reject the assignment if the script's `damage_range` is not `melee`.
5. WHEN a `UserScript` is assigned to a Ranged_Slot (party_slot ∈ {4, 5}), THE `Party_Manager` SHALL reject the assignment if the script's `damage_range` is not `ranged`.
6. IF a `party_slot` assignment violates the damage_range constraint, THEN THE `Party_Manager` SHALL raise a `ValueError` with a descriptive message identifying the slot and the required damage_range.

---

### Requirement 2: Party Composition Invariant

**User Story:** As a game designer, I want the party to always contain exactly 3 melee scripts and 2 ranged scripts when fully formed, so that combat balance is maintained.

#### Acceptance Criteria

1. WHEN a user's party is fully formed, THE `Party_Manager` SHALL ensure exactly 3 UserScripts have `party_slot` values in {1, 2, 3} and exactly 2 UserScripts have `party_slot` values in {4, 5}.
2. THE `Party_Manager` SHALL ensure that no two UserScripts belonging to the same user share the same `party_slot` value at any point in time.
3. THE `Party_Manager` SHALL ensure that a UserScript assigned to a Melee_Slot has `damage_range='melee'` and a UserScript assigned to a Ranged_Slot has `damage_range='ranged'`.
4. FOR ALL valid party states, swapping a script into a slot and then swapping the original script back SHALL result in a party state equivalent to the original (round-trip property).
5. FOR ALL valid party states, the count of scripts with `party_slot` in {1, 2, 3} SHALL be less than or equal to 3, and the count with `party_slot` in {4, 5} SHALL be less than or equal to 2.

---

### Requirement 3: Account Creation — Automatic Party Assignment

**User Story:** As a new player, I want my party to be automatically filled with valid scripts when I register, so that I can start playing immediately without manual setup.

#### Acceptance Criteria

1. WHEN a new user account is created, THE `UserManager` SHALL assign exactly 3 randomly selected scripts with `damage_range='melee'` to Melee_Slots 1, 2, and 3.
2. WHEN a new user account is created, THE `UserManager` SHALL assign exactly 2 randomly selected scripts with `damage_range='ranged'` to Ranged_Slots 4 and 5.
3. WHEN a new user account is created, THE `UserManager` SHALL ensure all 5 assigned scripts are distinct (no duplicate scripts in the starting party).
4. IF fewer than 3 melee scripts or fewer than 2 ranged scripts exist in the `Script` table at account creation time, THEN THE `UserManager` SHALL raise a `ValueError` and prevent account creation, logging a descriptive error message identifying the shortage.
5. WHEN a new user account is created, THE `UserManager` SHALL replace the current logic of adding 5 random scripts without positional assignment with the new positional assignment logic.

---

### Requirement 4: Existing Account Party Repair

**User Story:** As an existing player, I want my party to be automatically repaired to meet the new composition rules, so that I am not blocked from playing after the feature is deployed.

#### Acceptance Criteria

1. THE system SHALL provide a management command named `repair_parties` that inspects every user's party and fills any missing Melee_Slots or Ranged_Slots with randomly selected eligible scripts from the user's bench.
2. WHEN `repair_parties` runs and a user has fewer than 3 scripts in Melee_Slots, THE `repair_parties` command SHALL assign random melee scripts from the user's bench to fill the empty Melee_Slots.
3. WHEN `repair_parties` runs and a user has fewer than 2 scripts in Ranged_Slots, THE `repair_parties` command SHALL assign random ranged scripts from the user's bench to fill the empty Ranged_Slots.
4. WHEN `repair_parties` runs and a user's bench does not contain enough eligible scripts to fill a slot, THE `repair_parties` command SHALL create a new UserScript with a randomly selected eligible Script from the global Script pool and assign it to the empty slot.
5. WHEN `repair_parties` runs and a user has a script assigned to a slot whose `damage_range` does not match the slot type, THE `repair_parties` command SHALL move that script to the bench and fill the slot with an eligible script.
6. WHEN `repair_parties` runs and all scripts are already correctly placed in matching slot types with no empty slots, THE `repair_parties` command SHALL perform no modifications for that user.
7. THE system SHALL also perform the party repair check at user login, and IF a user's party is missing any slots, THEN THE system SHALL silently repair the party before rendering the Party_Page.

---

### Requirement 5: Party Management Page — Formation Display

**User Story:** As a player, I want to see my party arranged in a visual formation, so that I can understand the front-row and back-row layout at a glance.

#### Acceptance Criteria

1. THE `Party_Page` SHALL display a Formation_Display at the top of the page showing 5 party slots arranged as 3 front-row Melee_Slots and 2 back-row Ranged_Slots.
2. THE `Party_Page` SHALL display Efilwol in a fixed center-back position between the Ranged_Slots, visually distinct and labeled as non-swappable.
3. WHEN a Party_Slot is occupied, THE Formation_Display SHALL always show the script's name, role badge, and damage_range badge together within the slot card; all three elements are required and none may be omitted.
4. WHEN a Party_Slot is empty, THE Formation_Display SHALL show a placeholder indicating the required slot type (Melee or Ranged).
5. THE `Party_Page` SHALL replace the current scripts page at the same URL route, removing the flat list with add/remove buttons.

---

### Requirement 6: Party Management Page — Slot Selection and Bench Filtering

**User Story:** As a player, I want to click a party slot to select it and see only eligible scripts in the bench list below, so that I can quickly find valid replacements without scrolling through ineligible scripts.

#### Acceptance Criteria

1. WHEN a player clicks a Party_Slot in the Formation_Display, THE `Party_Page` SHALL highlight the Selected_Slot and filter the Bench_List to show only Eligible_Scripts for that slot type.
2. WHEN a Melee_Slot is selected, THE Bench_List SHALL display only UserScripts with `damage_range='melee'` that are not currently assigned to any party slot.
3. WHEN a Ranged_Slot is selected, THE Bench_List SHALL display only UserScripts with `damage_range='ranged'` that are not currently assigned to any party slot.
4. WHEN no slot is selected, THE Bench_List SHALL display all scripts not currently in the party, unfiltered.
5. WHEN a player clicks a script in the Bench_List while a slot is selected, THE `Party_Manager` SHALL swap the clicked script into the Selected_Slot and move the previously occupying script to the bench.
6. WHEN a swap is performed, THE `Party_Page` SHALL atomically update both the Formation_Display and the Bench_List to reflect the new party state; IF any part of the client-side update fails, THEN THE `Party_Page` SHALL revert all UI changes and display an error message to the player.
7. IF a player attempts to swap an ineligible script into a slot (e.g., via a direct URL manipulation), THEN THE `Party_Manager` SHALL reject the request, return an error response, and THE `Party_Page` SHALL display visual feedback indicating the reason for rejection without altering the current party state.

---

### Requirement 7: Slot Swap API

**User Story:** As a developer, I want a server-side endpoint to handle slot swaps atomically, so that party state is always consistent even if the client sends concurrent requests.

#### Acceptance Criteria

1. THE system SHALL provide a POST endpoint at `party/swap/` that accepts a `slot` (integer 1–5) and a `user_script_id` (the bench script to place into the slot).
2. WHEN the swap endpoint receives a valid request, THE `Party_Manager` SHALL atomically move the bench script into the specified slot and move the previously occupying script (if any) to the bench within a single database transaction.
3. IF the swap endpoint receives a `user_script_id` that does not belong to the authenticated user, THEN THE `Party_Manager` SHALL return an HTTP 403 response and the swap SHALL NOT be performed.
4. IF the swap endpoint receives a `slot` value outside the range 1–5, THEN THE `Party_Manager` SHALL return an HTTP 400 response with a descriptive error message.
5. IF the swap endpoint receives a script whose `damage_range` does not match the target slot type, THEN THE `Party_Manager` SHALL return an HTTP 400 response with a descriptive error message.
6. WHEN the swap endpoint completes successfully, THE system SHALL return an HTTP 200 response with the updated party state as JSON, including each slot's position, script name, role, and damage_range.
