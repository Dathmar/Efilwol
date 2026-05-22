from django.urls import path
from . import views


app_name = 'api'
urlpatterns = [
    path('game/attack/<int:source_id>/<int:target_id>/<int:attack_id>/<str:script_alignment>/', views.game_attack, name='game_attack'),
]
