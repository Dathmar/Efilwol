"""
Management command to seed and repair action data across the game.

Steps:
  1. Fix Action records where cast_time=0 but is_instant=False → set is_instant=True
  2. Fix Action records where base_power=0 → set to random int between 5 and 20
  3. Ensure each Script has at least 6 pool entries (add random Actions if needed)
  4. Ensure each NPCScript has at least 1 pool entry (add a random Action if empty)
  5. Backfill UserScript.actions for any UserScript with 0 assigned actions

All pool entry creation uses get_or_create to ensure idempotency.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from script.models import Action, NPCScript, NPCScriptPoolEntry, Script, ScriptPoolEntry
from users.models import UserScript


class Command(BaseCommand):
    help = (
        "Seed and repair action data: fix is_instant flags, fill base_power, "
        "ensure pool entries, and backfill UserScript actions."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== seed_actions ==="))

        with transaction.atomic():
            step1_count = self._fix_is_instant()
            step2_count = self._fix_base_power()
            step3_count = self._fill_script_pools()
            step4_count = self._fill_npc_script_pools()
            step5_count = self._backfill_user_script_actions()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Summary ==="))
        self.stdout.write(
            f"  Actions fixed (is_instant):          {step1_count}"
        )
        self.stdout.write(
            f"  Actions fixed (base_power):          {step2_count}"
        )
        self.stdout.write(
            f"  ScriptPoolEntries added:             {step3_count}"
        )
        self.stdout.write(
            f"  NPCScriptPoolEntries added:          {step4_count}"
        )
        self.stdout.write(
            f"  UserScripts backfilled (actions):    {step5_count}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))

    # ------------------------------------------------------------------
    # Step 1: Fix cast_time=0, is_instant=False → is_instant=True
    # ------------------------------------------------------------------
    def _fix_is_instant(self):
        """
        Use queryset .update() to bypass Action.full_clean() — these are
        legacy records that predate the is_instant field.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("Step 1: Fixing is_instant flags..."))
        qs = Action.objects.filter(cast_time=0, is_instant=False)
        count = qs.count()
        if count:
            qs.update(is_instant=True)
            self.stdout.write(
                f"  Updated {count} Action(s): cast_time=0, is_instant=False → is_instant=True"
            )
        else:
            self.stdout.write("  No Actions needed is_instant fix.")
        return count

    # ------------------------------------------------------------------
    # Step 2: Fix base_power=0 → random int 5–20
    # ------------------------------------------------------------------
    def _fix_base_power(self):
        """
        Use queryset .update() per record to bypass Action.full_clean().
        Each record gets its own random value.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("Step 2: Fixing base_power=0 values..."))
        zero_power_actions = list(Action.objects.filter(base_power=0).values_list('id', flat=True))
        count = len(zero_power_actions)
        if count:
            for action_id in zero_power_actions:
                new_power = random.randint(5, 20)
                Action.objects.filter(pk=action_id).update(base_power=new_power)
            self.stdout.write(
                f"  Updated {count} Action(s) with base_power=0 → random 5–20"
            )
        else:
            self.stdout.write("  No Actions needed base_power fix.")
        return count

    # ------------------------------------------------------------------
    # Step 3: Ensure each Script has ≥ 6 pool entries
    # ------------------------------------------------------------------
    def _fill_script_pools(self):
        """
        For each Script with fewer than 6 pool entries, add randomly selected
        Actions from the global Action table until the pool has at least 6.
        Uses get_or_create for idempotency.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("Step 3: Filling Script action pools..."))
        all_actions = list(Action.objects.all())
        if not all_actions:
            self.stdout.write(
                self.style.WARNING("  No Actions in database — skipping Script pool fill.")
            )
            return 0

        total_added = 0
        scripts = Script.objects.prefetch_related('pool_entries').all()

        for script in scripts:
            current_count = script.pool_entries.count()
            needed = 6 - current_count
            if needed <= 0:
                continue

            # Determine which actions are already in the pool
            existing_action_ids = set(
                script.pool_entries.values_list('action_id', flat=True)
            )
            # Candidates: actions not already in the pool
            candidates = [a for a in all_actions if a.id not in existing_action_ids]

            if not candidates:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Script '{script.name}': only {current_count} unique actions "
                        f"available globally — cannot reach 6."
                    )
                )
                continue

            # Sample without replacement (up to `needed` or all candidates)
            to_add = random.sample(candidates, min(needed, len(candidates)))
            added = 0
            for action in to_add:
                _, created = ScriptPoolEntry.objects.get_or_create(
                    script=script,
                    action=action,
                    defaults={'weight': 10},
                )
                if created:
                    added += 1

            total_added += added
            if added:
                self.stdout.write(
                    f"  Script '{script.name}': added {added} pool entry/entries "
                    f"(now {current_count + added})."
                )

        if total_added == 0:
            self.stdout.write("  All Scripts already have ≥ 6 pool entries.")
        return total_added

    # ------------------------------------------------------------------
    # Step 4: Ensure each NPCScript has ≥ 1 pool entry
    # ------------------------------------------------------------------
    def _fill_npc_script_pools(self):
        """
        For each NPCScript with an empty pool, add one random Action.
        Uses get_or_create for idempotency.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("Step 4: Filling NPCScript action pools..."))
        all_actions = list(Action.objects.all())
        if not all_actions:
            self.stdout.write(
                self.style.WARNING("  No Actions in database — skipping NPCScript pool fill.")
            )
            return 0

        total_added = 0
        npc_scripts = NPCScript.objects.prefetch_related('pool_entries').all()

        for npc in npc_scripts:
            if npc.pool_entries.count() > 0:
                continue

            action = random.choice(all_actions)
            _, created = NPCScriptPoolEntry.objects.get_or_create(
                npc_script=npc,
                action=action,
                defaults={'weight': 10},
            )
            if created:
                total_added += 1
                self.stdout.write(
                    f"  NPCScript '{npc.name}': added action '{action.name}'."
                )

        if total_added == 0:
            self.stdout.write("  All NPCScripts already have ≥ 1 pool entry.")
        return total_added

    # ------------------------------------------------------------------
    # Step 5: Backfill UserScript.actions for rows with < 6 actions
    # ------------------------------------------------------------------
    def _backfill_user_script_actions(self):
        """
        For each UserScript with fewer than 6 assigned actions, reassign
        actions from the script's pool using assign_actions().
        assign_actions() raises ValueError if the script's pool has < 6 entries,
        so Step 3 must run first.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("Step 5: Backfilling UserScript actions..."))
        from django.db.models import Count
        empty_user_scripts = (
            UserScript.objects
            .annotate(action_count=Count('actions'))
            .filter(action_count__lt=6)
            .select_related('script', 'user')
        )

        count = empty_user_scripts.count()
        if count == 0:
            self.stdout.write("  All UserScripts already have 6 actions assigned.")
            return 0

        success = 0
        errors = 0
        for us in empty_user_scripts:
            try:
                us.assign_actions()
                success += 1
                self.stdout.write(
                    f"  UserScript [{us.pk}] '{us.script.name}' for '{us.user}': "
                    f"assigned {us.actions.count()} actions."
                )
            except ValueError as exc:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  UserScript [{us.pk}] '{us.script.name}' for '{us.user}': "
                        f"FAILED — {exc}"
                    )
                )

        if errors:
            self.stdout.write(
                self.style.WARNING(
                    f"  {success} UserScript(s) backfilled, {errors} failed "
                    f"(pool too small — run Step 3 first or add more actions)."
                )
            )
        return success
