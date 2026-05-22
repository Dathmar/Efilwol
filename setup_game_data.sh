#!/bin/bash

echo "=========================================="
echo "ELIFWOL GAME DATA SETUP"
echo "=========================================="

# Activate virtual environment
source .venv/bin/activate

echo ""
echo "[1/4] Running migrations..."
python manage.py migrate

echo ""
echo "[2/4] Populating game data..."
python manage.py populate_game_data

echo ""
echo "[3/4] Checking database..."
python manage.py shell << EOF
from script.models import NPCScript, Script, Action
from users.models import User

print("\n📊 Database Status:")
print(f"  NPCs: {NPCScript.objects.count()}")
print(f"  Scripts: {Script.objects.count()}")
print(f"  Actions: {Action.objects.count()}")
print(f"  Users: {User.objects.count()}")

if NPCScript.objects.count() > 0:
    print("\n✅ Sample NPCs:")
    for npc in NPCScript.objects.all()[:3]:
        print(f"  • {npc.name} (HP: {npc.hp})")

if Script.objects.count() > 0:
    print("\n✅ Sample Scripts:")
    for script in Script.objects.all()[:3]:
        print(f"  • {script.name} ({script.role})")
EOF

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Create a user: python manage.py createsuperuser"
echo "  2. Start server: ./start-dev.sh"
echo "  3. Visit: http://localhost:8000/game/"
echo ""
