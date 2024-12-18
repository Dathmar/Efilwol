from django.contrib import admin

from script.models import Script, Spell


# Register your models here.
@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'damage_range', 'damage_specialization')


@admin.register(Spell)
class SpellAdmin(admin.ModelAdmin):
    list_display = ('name', 'mana_cost')