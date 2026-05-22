from django.contrib import admin
from .models import Stage


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'is_demo', 'enemy_count', 'party_size', 'xp_reward', 'min_party_level')
    list_filter = ('is_demo',)
    ordering = ('order',)
    filter_horizontal = ('enemy_pool', 'demo_party_pool')
