from django.contrib import admin

from script.models import Script, Action, NPCScript, ScriptPoolEntry, NPCScriptPoolEntry


# Register your models here.
@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'damage_range', 'damage_specialization')


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_instant', 'base_power', 'cast_time', 'cooldown')
    list_editable = ('is_instant', 'base_power', 'cast_time', 'cooldown')
    list_filter = ('type', 'is_instant')
    fields = ('name', 'description', 'type', 'is_instant', 'cast_time',
              'base_power', 'cooldown', 'duration', 'max_targets', 'attribute_modified')


@admin.register(NPCScript)
class NPCScriptAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(ScriptPoolEntry)
class ScriptPoolEntryAdmin(admin.ModelAdmin):
    list_display = ('script', 'action', 'weight')
    list_editable = ('weight',)


@admin.register(NPCScriptPoolEntry)
class NPCScriptPoolEntryAdmin(admin.ModelAdmin):
    list_display = ('npc_script', 'action', 'weight')
    list_editable = ('weight',)