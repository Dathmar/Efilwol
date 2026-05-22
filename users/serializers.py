from rest_framework import serializers
from .models import UserScript

class UserScriptSerializer(serializers.ModelSerializer):
    script_id = serializers.IntegerField(source='script.id', read_only=True)
    script_name = serializers.CharField(source='script.name', read_only=True)
    action_ids = serializers.SerializerMethodField()

    def get_action_ids(self, instance):
        return list(instance.actions.values_list('id', flat=True))

    class Meta:
        model = UserScript
        fields = ('id', 'script', 'script_id', 'script_name', 'in_party', 'hp', 'mana', 'action_ids')

