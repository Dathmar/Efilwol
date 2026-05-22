from rest_framework import serializers
from .models import Script, Spell

class ScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = ('id', 'name', 'description', 'role', 'damage_range', 'damage_specialization', 'health')

class SpellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spell
        fields = ('id', 'name', 'description', 'modifier', 'type', 'mana_cost', 'cooldown', 'duration', 'scope', 'attribute_modified')