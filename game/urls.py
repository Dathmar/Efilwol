from django.urls import path
from . import views

app_name = 'game'
urlpatterns = [
    path('', views.index, name='index'),
    path('play/', views.game, name='game'),
    path('play/<int:stage_id>/', views.game, name='game_stage'),
]
