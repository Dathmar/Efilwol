#!/usr/bin/env python
"""
Test script to verify game data and functionality
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Efilwol.settings')
os.environ['DJANGO_ENVIRONMENT'] = 'development'
django.setup()

from script.models import NPCScript, Script, Action
from users.models import User, UserScript
from django.contrib.auth import get_user_model

def test_database():
    """Test that database has required data"""
    print("=" * 60)
    print("DATABASE TEST")
    print("=" * 60)
    
    # Test NPCs
    npc_count = NPCScript.objects.count()
    print(f"\n✓ NPCs in database: {npc_count}")
    if npc_count == 0:
        print("  ❌ ERROR: No NPCs found! Run: python manage.py populate_game_data")
        return False
    
    print("\n  NPCs:")
    for npc in NPCScript.objects.all()[:5]:
        print(f"    - {npc.name} (HP: {npc.hp}, Attack: {npc.attack})")
    
    # Test Scripts
    script_count = Script.objects.count()
    print(f"\n✓ Player Scripts in database: {script_count}")
    if script_count > 0:
        print("\n  Scripts:")
        for script in Script.objects.all()[:5]:
            print(f"    - {script.name} ({script.role}, {script.damage_range})")
    
    # Test Actions
    action_count = Action.objects.count()
    print(f"\n✓ Actions in database: {action_count}")
    if action_count > 0:
        print("\n  Actions:")
        for action in Action.objects.all()[:5]:
            print(f"    - {action.name} (Power: {action.base_power})")
    
    # Test Users
    user_count = User.objects.count()
    print(f"\n✓ Users in database: {user_count}")
    
    return True

def test_user_scripts():
    """Test user scripts"""
    print("\n" + "=" * 60)
    print("USER SCRIPTS TEST")
    print("=" * 60)
    
    users = User.objects.all()
    if not users.exists():
        print("\n❌ No users found. Create a user first:")
        print("   python manage.py createsuperuser")
        return False
    
    for user in users[:3]:
        user_scripts = UserScript.objects.filter(user=user)
        party_scripts = user_scripts.filter(in_party=True)
        
        print(f"\n✓ User: {user.email}")
        print(f"  Total scripts: {user_scripts.count()}")
        print(f"  In party: {party_scripts.count()}")
        
        if party_scripts.exists():
            print("  Party members:")
            for us in party_scripts:
                print(f"    - {us.script.name} (HP: {us.hp})")
    
    return True

def test_game_view():
    """Test game view logic"""
    print("\n" + "=" * 60)
    print("GAME VIEW TEST")
    print("=" * 60)
    
    from script.serializers import NPCScriptSerializer
    
    # Test getting random enemies
    print("\n✓ Testing enemy selection...")
    enemies = []
    for i in range(3):
        npc = NPCScript.objects.order_by('?').first()
        if npc:
            serialized = NPCScriptSerializer(npc, many=False)
            enemies.append(serialized.data)
            print(f"  Enemy {i+1}: {npc.name}")
        else:
            print(f"  ❌ Could not get enemy {i+1}")
    
    if len(enemies) == 3:
        print("\n✅ Successfully got 3 enemies")
        return True
    else:
        print(f"\n❌ Only got {len(enemies)} enemies")
        return False

def create_test_user():
    """Create a test user with scripts"""
    print("\n" + "=" * 60)
    print("CREATE TEST USER")
    print("=" * 60)
    
    email = "test@elifwol.com"
    
    # Check if user exists
    user = User.objects.filter(email=email).first()
    if user:
        print(f"\n✓ Test user already exists: {email}")
    else:
        user = User.objects.create_user(email=email, password="testpass123")
        print(f"\n✓ Created test user: {email}")
    
    # Add scripts to user
    user_scripts = UserScript.objects.filter(user=user)
    if user_scripts.count() == 0:
        print("\n✓ Adding scripts to user...")
        scripts = Script.objects.all()[:3]
        for script in scripts:
            UserScript.objects.create(
                user=user,
                script=script,
                in_party=True,
                hp=script.hp
            )
            print(f"  Added: {script.name}")
    else:
        print(f"\n✓ User already has {user_scripts.count()} scripts")
    
    party = UserScript.objects.filter(user=user, in_party=True)
    print(f"\n✓ User has {party.count()} scripts in party")
    
    return user

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ELIFWOL GAME TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database
    results.append(("Database", test_database()))
    
    # Test 2: Game View
    results.append(("Game View", test_game_view()))
    
    # Test 3: User Scripts
    results.append(("User Scripts", test_user_scripts()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("\nYou can now:")
        print("  1. Start the server: ./start-dev.sh")
        print("  2. Visit: http://localhost:8000/game/")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == '__main__':
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
