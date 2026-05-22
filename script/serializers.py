from rest_framework import serializers
from .models import Script, Action, NPCScript

class ScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = ('id', 'name', 'description', 'role', 'damage_range', 'damage_specialization', 'hp')


class NPCScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = NPCScript
        fields = ('id', 'name', 'description', 'damage_specialization', 'hp')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('id', 'name', 'description', 'base_power', 'type', 'cast_time', 'cooldown', 'duration', 'attribute_modified')