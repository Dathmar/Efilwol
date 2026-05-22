from django.contrib import admin

from .models import User, UserScript, UserPreferences, Suggestion


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email',)
    search_fields = ('email',)


@admin.register(UserScript)
class UserScriptAdmin(admin.ModelAdmin):
    list_display  = ('user', 'script', 'party_slot', 'in_party', 'hp', 'mana')
    list_editable = ('party_slot', 'hp', 'mana')
    list_filter   = ('in_party', 'party_slot')
    search_fields = ('user__email', 'script__name')
    readonly_fields = ('in_party',)
    fields  = ('user', 'script', 'party_slot', 'in_party', 'hp', 'mana', 'actions')
    ordering = ('user', 'party_slot')


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display  = ('user', 'confirm_cast_cancel')
    list_editable = ('confirm_cast_cancel',)
    search_fields = ('user__email',)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'user', 'created_at')
    list_filter   = ('category',)
    search_fields = ('title', 'body', 'user__email')
    readonly_fields = ('user', 'created_at')
    ordering = ('-created_at',)
