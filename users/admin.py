from django.contrib import admin

from .models import User, UserScript


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', )


@admin.register(UserScript)
class UserScriptAdmin(admin.ModelAdmin):
    list_display = ('user', 'script', 'in_party')