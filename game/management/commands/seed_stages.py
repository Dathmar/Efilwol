"""
Seed initial game stages.
Safe to run multiple times — uses get_or_create.
"""
from django.core.management.base import BaseCommand
from game.models import Stage
from script.models import NPCScript, Script


class Command(BaseCommand):
    help = 'Seeds initial Stage data including the demo stage'

    def handle(self, *args, **options):
        self.stdout.write('Seeding stages...')

        all_npcs = list(NPCScript.objects.all())
        all_scripts = list(Script.objects.all())

        if not all_npcs:
            self.stdout.write(self.style.ERROR(
                'No NPCs found. Run: python manage.py populate_game_data first.'
            ))
            return

        if not all_scripts:
            self.stdout.write(self.style.ERROR(
                'No Scripts found. Run: python manage.py populate_game_data first.'
            ))
            return

        # ── Stage 1: Demo ────────────────────────────────────────────────
        demo, created = Stage.objects.get_or_create(
            order=1,
            defaults={
                'name': 'The Outskirts',
                'description': (
                    'A group of wandering enemies has been spotted near the village. '
                    'Drive them back — no experience required.'
                ),
                'is_demo': True,
                'enemy_count': 3,
                'party_size': 5,
                'xp_reward': 0,
                'min_party_level': 1,
            }
        )
        if created:
            demo.enemy_pool.set(all_npcs)
            demo.demo_party_pool.set(all_scripts)
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ Created demo stage: "{demo.name}" '
                f'({len(all_npcs)} enemies, {len(all_scripts)} party scripts)'
            ))
        else:
            self.stdout.write(f'  ℹ️  Demo stage already exists: "{demo.name}"')

        # ── Stage 2: First real stage ────────────────────────────────────
        stage2, created = Stage.objects.get_or_create(
            order=2,
            defaults={
                'name': 'The Dark Forest',
                'description': (
                    'Deeper threats lurk in the forest. '
                    'Your party must be ready.'
                ),
                'is_demo': False,
                'enemy_count': 3,
                'xp_reward': 100,
                'min_party_level': 1,
            }
        )
        if created:
            stage2.enemy_pool.set(all_npcs)
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ Created stage 2: "{stage2.name}"'
            ))
        else:
            self.stdout.write(f'  ℹ️  Stage 2 already exists: "{stage2.name}"')

        self.stdout.write(self.style.SUCCESS('\nDone. Stages in database:'))
        for stage in Stage.objects.all():
            tag = ' [DEMO]' if stage.is_demo else ''
            self.stdout.write(f'  {stage.order}. {stage.name}{tag}')
