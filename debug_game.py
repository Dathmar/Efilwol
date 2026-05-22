#!/usr/bin/env python
"""
Comprehensive game debugging script
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Efilwol.settings')
os.environ['DJANGO_ENVIRONMENT'] = 'development'

print("=" * 70)
print("ELIFWOL GAME DEBUG SCRIPT")
print("=" * 70)

try:
    print("\n[1/6] Setting up Django...")
    django.setup()
    print("✅ Django setup complete")
    
    print("\n[2/6] Importing models...")
    from script.models import NPCScript, Script, Action
    from users.models import User, UserScript
    print("✅ Models imported")
    
    print("\n[3/6] Checking database...")
    npc_count = NPCScript.objects.count()
    script_count = Script.objects.count()
    action_count = Action.objects.count()
    user_count = User.objects.count()
    
    print(f"  📊 NPCs: {npc_count}")
    print(f"  📊 Scripts: {script_count}")
    print(f"  📊 Actions: {action_count}")
    print(f"  📊 Users: {user_count}")
    
    if npc_count == 0:
        print("\n❌ NO NPCs FOUND!")
        print("   Run: python manage.py populate_game_data")
        sys.exit(1)
    
    print("\n[4/6] Sample NPCs:")
    for npc in NPCScript.objects.all()[:5]:
        print(f"  • {npc.name} - HP: {npc.hp}, Attack: {npc.attack}")
    
    print("\n[5/6] Sample Scripts:")
    for script in Script.objects.all()[:5]:
        print(f"  • {script.name} - {script.role}/{script.damage_range}, HP: {script.hp}")
    
    print("\n[6/6] Checking users with party...")
    if user_count == 0:
        print("  ⚠️  No users found. Create one with:")
        print("     python manage.py createsuperuser")
    else:
        for user in User.objects.all()[:3]:
            party = UserScript.objects.filter(user=user, in_party=True)
            print(f"  • {user.email}: {party.count()} party members")
            if party.count() == 0:
                print(f"    ⚠️  User has no party! They need to add scripts.")
    
    print("\n" + "=" * 70)
    print("✅ ALL CHECKS PASSED - Database is ready!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Start server: ./start-dev.sh")
    print("  2. Visit: http://localhost:8000/game/")
    print("  3. Check browser console for Alpine.js logs")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
