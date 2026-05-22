"""
Management command to populate the database with initial game data.
"""

from django.core.management.base import BaseCommand
from script.models import NPCScript, Script, Action, ScriptPoolEntry, NPCScriptPoolEntry


class Command(BaseCommand):
    help = 'Populates the database with initial game data (enemies, scripts, actions)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting game data population...'))
        
        # Create Actions first
        self.create_actions()
        
        # Create NPCs (Enemies)
        self.create_npcs()
        
        # Create Player Scripts
        self.create_player_scripts()
        
        self.stdout.write(self.style.SUCCESS('✅ Game data population complete!'))

    def create_actions(self):
        """Create basic actions for combat"""
        self.stdout.write('Creating actions...')
        
        actions_data = [
            {
                'name': 'Basic Attack',
                'description': 'A simple physical attack',
                'base_power': 20,
                'type': 'physical',
                'cast_time': 1.0,
                'cooldown': 1.0,
                'max_targets': 1,
                'attribute_modified': 'health'
            },
            {
                'name': 'Heavy Strike',
                'description': 'A powerful physical attack',
                'base_power': 40,
                'type': 'physical',
                'cast_time': 2.0,
                'cooldown': 3.0,
                'max_targets': 1,
                'attribute_modified': 'health'
            },
            {
                'name': 'Fire Bolt',
                'description': 'Launch a bolt of fire',
                'base_power': 30,
                'type': 'fire',
                'cast_time': 1.5,
                'cooldown': 2.0,
                'max_targets': 1,
                'attribute_modified': 'health'
            },
            {
                'name': 'Ice Shard',
                'description': 'Shoot a shard of ice',
                'base_power': 25,
                'type': 'ice',
                'cast_time': 1.5,
                'cooldown': 2.0,
                'max_targets': 1,
                'attribute_modified': 'health'
            },
            {
                'name': 'Lightning Strike',
                'description': 'Call down lightning',
                'base_power': 35,
                'type': 'lightning',
                'cast_time': 2.0,
                'cooldown': 3.0,
                'max_targets': 1,
                'attribute_modified': 'health'
            },
        ]
        
        for action_data in actions_data:
            action, created = Action.objects.get_or_create(
                name=action_data['name'],
                defaults=action_data
            )
            if created:
                self.stdout.write(f'  ✅ Created action: {action.name}')
            else:
                self.stdout.write(f'  ℹ️  Action already exists: {action.name}')

    def create_npcs(self):
        """Create NPC enemies"""
        self.stdout.write('Creating NPCs (enemies)...')
        
        npcs_data = [
            {
                'name': 'Goblin Warrior',
                'description': 'A small but fierce goblin',
                'damage_specialization': 'physical',
                'hp': 80,
                'defence': 5.0,
                'resistance': 3.0,
                'attack': 15.0,
                'speed': 8.0,
                'luck': 5.0,
            },
            {
                'name': 'Dark Mage',
                'description': 'A mage wielding dark magic',
                'damage_specialization': 'dark',
                'hp': 60,
                'defence': 3.0,
                'resistance': 8.0,
                'attack': 20.0,
                'speed': 6.0,
                'luck': 7.0,
            },
            {
                'name': 'Fire Elemental',
                'description': 'A being of pure flame',
                'damage_specialization': 'fire',
                'hp': 70,
                'defence': 4.0,
                'resistance': 10.0,
                'attack': 18.0,
                'speed': 7.0,
                'luck': 6.0,
            },
            {
                'name': 'Ice Golem',
                'description': 'A massive creature of ice',
                'damage_specialization': 'ice',
                'hp': 120,
                'defence': 10.0,
                'resistance': 8.0,
                'attack': 12.0,
                'speed': 3.0,
                'luck': 4.0,
            },
            {
                'name': 'Shadow Assassin',
                'description': 'A deadly assassin from the shadows',
                'damage_specialization': 'dark',
                'hp': 50,
                'defence': 4.0,
                'resistance': 5.0,
                'attack': 25.0,
                'speed': 12.0,
                'luck': 9.0,
            },
            {
                'name': 'Thunder Beast',
                'description': 'A beast crackling with electricity',
                'damage_specialization': 'lightning',
                'hp': 90,
                'defence': 6.0,
                'resistance': 7.0,
                'attack': 22.0,
                'speed': 9.0,
                'luck': 6.0,
            },
            {
                'name': 'Poison Spider',
                'description': 'A giant spider with venomous fangs',
                'damage_specialization': 'poison',
                'hp': 65,
                'defence': 5.0,
                'resistance': 6.0,
                'attack': 16.0,
                'speed': 10.0,
                'luck': 7.0,
            },
            {
                'name': 'Stone Guardian',
                'description': 'An ancient guardian made of stone',
                'damage_specialization': 'earth',
                'hp': 150,
                'defence': 15.0,
                'resistance': 10.0,
                'attack': 10.0,
                'speed': 2.0,
                'luck': 3.0,
            },
        ]
        
        basic_attack = Action.objects.filter(name='Basic Attack').first()
        
        for npc_data in npcs_data:
            npc, created = NPCScript.objects.get_or_create(
                name=npc_data['name'],
                defaults=npc_data
            )
            if created:
                if basic_attack:
                    NPCScriptPoolEntry.objects.get_or_create(npc_script=npc, action=basic_attack)
                self.stdout.write(f'  ✅ Created NPC: {npc.name}')
            else:
                self.stdout.write(f'  ℹ️  NPC already exists: {npc.name}')

    def create_player_scripts(self):
        """Create player scripts"""
        self.stdout.write('Creating player scripts...')
        
        scripts_data = [
            {
                'name': 'Knight',
                'description': 'A heavily armored warrior',
                'damage_specialization': 'physical',
                'hp': 120,
                'defence': 12.0,
                'resistance': 6.0,
                'attack': 15.0,
                'speed': 5.0,
                'luck': 5.0,
                'role': 'tank',
                'damage_range': 'melee',
            },
            {
                'name': 'Archer',
                'description': 'A skilled ranged fighter',
                'damage_specialization': 'physical',
                'hp': 80,
                'defence': 5.0,
                'resistance': 5.0,
                'attack': 20.0,
                'speed': 10.0,
                'luck': 8.0,
                'role': 'dps',
                'damage_range': 'ranged',
            },
            {
                'name': 'Fire Mage',
                'description': 'A mage specializing in fire magic',
                'damage_specialization': 'fire',
                'hp': 70,
                'defence': 3.0,
                'resistance': 10.0,
                'attack': 25.0,
                'speed': 7.0,
                'luck': 6.0,
                'role': 'dps',
                'damage_range': 'ranged',
            },
            {
                'name': 'Ice Mage',
                'description': 'A mage specializing in ice magic',
                'damage_specialization': 'ice',
                'hp': 70,
                'defence': 3.0,
                'resistance': 10.0,
                'attack': 23.0,
                'speed': 7.0,
                'luck': 6.0,
                'role': 'dps',
                'damage_range': 'ranged',
            },
            {
                'name': 'Berserker',
                'description': 'A fierce melee fighter',
                'damage_specialization': 'physical',
                'hp': 100,
                'defence': 8.0,
                'resistance': 4.0,
                'attack': 22.0,
                'speed': 8.0,
                'luck': 7.0,
                'role': 'dps',
                'damage_range': 'melee',
            },
            {
                'name': 'Paladin',
                'description': 'A holy warrior',
                'damage_specialization': 'holy',
                'hp': 110,
                'defence': 10.0,
                'resistance': 8.0,
                'attack': 16.0,
                'speed': 6.0,
                'luck': 7.0,
                'role': 'tank',
                'damage_range': 'melee',
            },
        ]
        
        basic_attack = Action.objects.filter(name='Basic Attack').first()
        
        for script_data in scripts_data:
            script, created = Script.objects.get_or_create(
                name=script_data['name'],
                defaults=script_data
            )
            if created:
                if basic_attack:
                    ScriptPoolEntry.objects.get_or_create(script=script, action=basic_attack)
                self.stdout.write(f'  ✅ Created script: {script.name}')
            else:
                self.stdout.write(f'  ℹ️  Script already exists: {script.name}')
