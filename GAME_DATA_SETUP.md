# 🎮 Game Data Setup Guide

## Issue: All Enemies Are Dead

If you see all enemies as dead when visiting `/game/`, it means the database has no NPC (enemy) data.

## Solution: Populate Game Data

Run the management command to populate the database with initial game data:

```bash
python manage.py populate_game_data
```

Or with the virtual environment:

```bash
source .venv/bin/activate
python manage.py populate_game_data
```

## What Gets Created

### Actions (5 total)
- **Basic Attack** - Simple physical attack (20 damage)
- **Heavy Strike** - Powerful physical attack (40 damage)
- **Fire Bolt** - Fire magic attack (30 damage)
- **Ice Shard** - Ice magic attack (25 damage)
- **Lightning Strike** - Lightning attack (35 damage)

### NPCs / Enemies (8 total)
1. **Goblin Warrior** - Physical damage, 80 HP
2. **Dark Mage** - Dark magic, 60 HP
3. **Fire Elemental** - Fire damage, 70 HP
4. **Ice Golem** - Ice damage, 120 HP (tank)
5. **Shadow Assassin** - Dark damage, 50 HP (fast)
6. **Thunder Beast** - Lightning damage, 90 HP
7. **Poison Spider** - Poison damage, 65 HP
8. **Stone Guardian** - Earth damage, 150 HP (tank)

### Player Scripts (6 total)
1. **Knight** - Tank, melee, 120 HP
2. **Archer** - DPS, ranged, 80 HP
3. **Fire Mage** - DPS, ranged, 70 HP
4. **Ice Mage** - DPS, ranged, 70 HP
5. **Berserker** - DPS, melee, 100 HP
6. **Paladin** - Tank, melee, 110 HP

## Verification

After running the command, you should see output like:

```
Starting game data population...
Creating actions...
  ✅ Created action: Basic Attack
  ✅ Created action: Heavy Strike
  ...
Creating NPCs (enemies)...
  ✅ Created NPC: Goblin Warrior
  ✅ Created NPC: Dark Mage
  ...
Creating player scripts...
  ✅ Created script: Knight
  ✅ Created script: Archer
  ...
✅ Game data population complete!
```

## Check Database

You can verify the data was created:

```bash
python manage.py shell
```

Then in the shell:

```python
from script.models import NPCScript, Script, Action

# Check NPCs
print(f"NPCs: {NPCScript.objects.count()}")
for npc in NPCScript.objects.all():
    print(f"  - {npc.name}")

# Check Scripts
print(f"Scripts: {Script.objects.count()}")
for script in Script.objects.all():
    print(f"  - {script.name}")

# Check Actions
print(f"Actions: {Action.objects.count()}")
for action in Action.objects.all():
    print(f"  - {action.name}")
```

## Adding Your Own Data

### Add a New Enemy

```python
from script.models import NPCScript

enemy = NPCScript.objects.create(
    name='Dragon',
    description='A fearsome dragon',
    damage_specialization='fire',
    hp=200,
    defence=15.0,
    resistance=12.0,
    attack=30.0,
    speed=5.0,
    luck=8.0,
)
```

### Add a New Player Script

```python
from script.models import Script

script = Script.objects.create(
    name='Wizard',
    description='A powerful wizard',
    damage_specialization='lightning',
    hp=75,
    defence=4.0,
    resistance=12.0,
    attack=28.0,
    speed=8.0,
    luck=7.0,
    role='dps',
    damage_range='ranged',
)
```

## Automatic Check

The game view now automatically checks if there are enemies in the database:

- **No enemies:** Redirects to homepage with a warning message
- **Less than 3 enemies:** Shows a warning but still loads the game
- **3+ enemies:** Game loads normally

## Re-running the Command

The command is safe to run multiple times. It will:
- ✅ Skip existing data (won't create duplicates)
- ✅ Only create missing data
- ✅ Show which items were created vs. already existed

## Troubleshooting

### Command not found

Make sure you're in the project directory and virtual environment is activated:

```bash
cd /path/to/Efilwol
source .venv/bin/activate
python manage.py populate_game_data
```

### No module named 'script.management'

Make sure the management command files were created:

```bash
ls -la script/management/commands/
```

You should see:
- `__init__.py`
- `populate_game_data.py`

### Database errors

Run migrations first:

```bash
python manage.py migrate
```

## Quick Start Workflow

For a fresh setup:

```bash
# 1. Run migrations
python manage.py migrate

# 2. Populate game data
python manage.py populate_game_data

# 3. Create superuser (optional)
python manage.py createsuperuser

# 4. Start server
./start-dev.sh

# 5. Visit http://localhost:8000/game/
```

## Files Created

- `script/management/__init__.py`
- `script/management/commands/__init__.py`
- `script/management/commands/populate_game_data.py`

## Updated Files

- `game/views.py` - Added check for empty database

---

**Now your game should have enemies to fight! 🎮⚔️**
