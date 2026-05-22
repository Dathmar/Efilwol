#!/bin/bash

echo "=========================================="
echo "ELIFWOL COMPLETE GAME SETUP & TEST"
echo "=========================================="

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "❌ Virtual environment not found!"
    echo "   Run: python -m venv .venv"
    exit 1
fi

echo ""
echo "[1/5] Running migrations..."
python manage.py migrate --no-input

echo ""
echo "[2/5] Populating game data..."
python manage.py populate_game_data

echo ""
echo "[3/5] Creating test user with party..."
python create_test_user.py

echo ""
echo "[4/5] Verifying setup..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Efilwol.settings')
os.environ['DJANGO_ENVIRONMENT'] = 'development'
django.setup()

from script.models import NPCScript, Script, Action
from users.models import User, UserScript

print('\n📊 Final Database Status:')
print(f'  NPCs: {NPCScript.objects.count()}')
print(f'  Scripts: {Script.objects.count()}')
print(f'  Actions: {Action.objects.count()}')
print(f'  Users: {User.objects.count()}')

users_with_party = 0
for user in User.objects.all():
    party = UserScript.objects.filter(user=user, in_party=True)
    if party.count() > 0:
        users_with_party += 1
        print(f'\n  User: {user.email}')
        print(f'    Party members: {party.count()}')
        for us in party:
            print(f'      - {us.script.name}')

if users_with_party == 0:
    print('\n⚠️  No users have party members!')
else:
    print(f'\n✅ {users_with_party} user(s) ready to play!')
"

echo ""
echo "[5/5] Setup complete!"
echo ""
echo "=========================================="
echo "READY TO PLAY!"
echo "=========================================="
echo ""
echo "Test credentials:"
echo "  Email: test@elifwol.com"
echo "  Password: testpass123"
echo ""
echo "Next steps:"
echo "  1. Start server: ./start-dev.sh"
echo "  2. Visit: http://localhost:8000/users/login/"
echo "  3. Login and go to: http://localhost:8000/game/"
echo "  4. Open browser console (F12) to see initialization logs"
echo ""
echo "If you see issues, check: GAME_TESTING_GUIDE.md"
echo ""
