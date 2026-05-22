#!/usr/bin/env python
"""
Create a test user with party members for game testing
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Efilwol.settings')
os.environ['DJANGO_ENVIRONMENT'] = 'development'

django.setup()

from script.models import Script
from users.models import User, UserScript

def create_test_user():
    """Create test user with party"""
    email = "test@elifwol.com"
    password = "testpass123"
    
    print("=" * 60)
    print("CREATE TEST USER WITH PARTY")
    print("=" * 60)
    
    # Check if user exists
    user = User.objects.filter(email=email).first()
    if user:
        print(f"\n✓ Test user already exists: {email}")
    else:
        user = User.objects.create_user(email=email, password=password)
        print(f"\n✓ Created test user: {email}")
        print(f"  Password: {password}")
    
    # Check if user has scripts
    existing_scripts = UserScript.objects.filter(user=user)
    if existing_scripts.count() > 0:
        print(f"\n✓ User already has {existing_scripts.count()} scripts")
        party = existing_scripts.filter(in_party=True)
        print(f"  {party.count()} in party:")
        for us in party:
            print(f"    - {us.script.name} (HP: {us.hp})")
        return user
    
    # Add scripts to user
    print("\n✓ Adding scripts to user...")
    scripts = Script.objects.all()[:4]  # Get first 4 scripts
    
    if scripts.count() == 0:
        print("\n❌ No scripts found in database!")
        print("   Run: python manage.py populate_game_data")
        return None
    
    for script in scripts:
        UserScript.objects.create(
            user=user,
            script=script,
            in_party=True,
            hp=script.hp
        )
        print(f"  Added: {script.name} ({script.role}, HP: {script.hp})")
    
    print(f"\n✅ Test user ready!")
    print(f"\nLogin credentials:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"\nYou can now:")
    print(f"  1. Start server: ./start-dev.sh")
    print(f"  2. Visit: http://localhost:8000/users/login/")
    print(f"  3. Login and go to: http://localhost:8000/game/")
    
    return user

if __name__ == '__main__':
    try:
        create_test_user()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
