#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Efilwol.settings')
os.environ['DJANGO_ENVIRONMENT'] = 'development'

try:
    django.setup()
    from script.models import NPCScript, Script, Action
    from users.models import User
    
    print("Database Check:")
    print(f"NPCs: {NPCScript.objects.count()}")
    print(f"Scripts: {Script.objects.count()}")
    print(f"Actions: {Action.objects.count()}")
    print(f"Users: {User.objects.count()}")
    
    if NPCScript.objects.count() > 0:
        print("\nSample NPCs:")
        for npc in NPCScript.objects.all()[:3]:
            print(f"  - {npc.name} (HP: {npc.hp})")
    
    if Script.objects.count() > 0:
        print("\nSample Scripts:")
        for script in Script.objects.all()[:3]:
            print(f"  - {script.name} ({script.role})")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
