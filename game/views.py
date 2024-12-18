from django.shortcuts import render
from django.apps import apps
from script.models import Script
from random import randint
# Create your views here.
def index(request):
    return render(request, 'game/index.html')

def game(request):
    enemies = []
    for _ in range(3):
        enemies.append(
            {
                'script': Script.objects.order_by('?').first(),
                'hp': randint(100, 200)
            }
        )

    lowlife = {
            'script': {
                'name': 'Efilwol'
            },
            'hp': randint(100, 200)
        }
    context = {
        'enemy_scripts': enemies,
        'party_scripts': apps.get_model('users', 'UserScript').objects.filter(user=request.user,  in_party=True),
        'lowlife': lowlife,

    }
    return render(request, 'game/game.html', context)