from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
class BaseScript(models.Model):
    DAMAGE_SPECIALIZATION_CHOICES = [
        ('physical', 'Physical'),
        ('lightning', 'Lightning'),
        ('fire', 'Fire'),
        ('ice', 'Ice'),
        ('earth', 'Earth'),
        ('water', 'Water'),
        ('poison', 'Poison'),
        ('necrotic', 'Necrotic'),
        ('holy', 'Holy'),
        ('dark', 'Dark'),

        ('none', 'None'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    damage_specialization = models.CharField(max_length=20, choices=DAMAGE_SPECIALIZATION_CHOICES)
    hp = models.IntegerField()
    defence = models.DecimalField(max_digits=3, decimal_places=1)
    resistance = models.DecimalField(max_digits=3, decimal_places=1)
    attack = models.DecimalField(max_digits=3, decimal_places=1)
    speed = models.DecimalField(max_digits=3, decimal_places=1)
    luck = models.DecimalField(max_digits=3, decimal_places=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.name}'


class Script(BaseScript):
    ROLE_CHOICES = [
        ('tank', 'Tank'),
        ('dps', 'DPS'),
    ]

    DAMAGE_RANGE_CHOICES = [
        ('melee', 'Melee'),
        ('ranged', 'Ranged'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    damage_range = models.CharField(max_length=10, choices=DAMAGE_RANGE_CHOICES)
    action_pool = models.ManyToManyField('Action', through='ScriptPoolEntry', blank=True)

    def __str__(self):
        return f'{self.name} | {self.role} | {self.damage_range} | {self.damage_specialization}'


class NPCScript(BaseScript):
    action_pool = models.ManyToManyField('Action', through='NPCScriptPoolEntry', blank=True)


class ScriptPoolEntry(models.Model):
    script = models.ForeignKey(Script, on_delete=models.CASCADE, related_name='pool_entries')
    action = models.ForeignKey('Action', on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = ('script', 'action')

    def __str__(self):
        return f'{self.script.name} → {self.action.name} (weight={self.weight})'


class NPCScriptPoolEntry(models.Model):
    npc_script = models.ForeignKey(NPCScript, on_delete=models.CASCADE, related_name='pool_entries')
    action = models.ForeignKey('Action', on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = ('npc_script', 'action')

    def __str__(self):
        return f'{self.npc_script.name} → {self.action.name} (weight={self.weight})'



class Action(models.Model):
    TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('lightning', 'Lightning'),
        ('fire', 'Fire'),
        ('ice', 'Ice'),
        ('earth', 'Earth'),
        ('water', 'Water'),
        ('poison', 'Poison'),
        ('necrotic', 'Necrotic'),
        ('holy', 'Holy'),
        ('dark', 'Dark'),

        ('healing', 'Healing'),
        ('buff', 'Buff'),
        ('debuff', 'Debuff'),
    ]

    ATTRIBUTE_MODIFIED_CHOICES = [
        ('health', 'Health'),
        ('mana', 'Mana'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()

    base_power = models.IntegerField(
        help_text="Numerical scaling factor for this spell e.g. the damage or healing done. "
                  "But can also be the strength of a buff",
        default=0
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='physical')
    is_instant = models.BooleanField(
        default=False,
        help_text="If True, this action fires instantly (cast_time must be 0)."
    )
    cast_time = models.DecimalField(
        help_text="Time in seconds to cast the spell.  For damage or healing this will be the cast time",
        null=True, blank=True,
        default=0,
        decimal_places=1,
        max_digits=4
    )
    cooldown = models.DecimalField(
        default=0,
        decimal_places=1,
        max_digits=4
    )
    duration = models.IntegerField(
        help_text="Duration of the spell in seconds.  For damage or healing this will be the hot/dot time",
        null=True, blank=True
    )
    max_targets = models.IntegerField(default=1)
    attribute_modified = models.CharField(max_length=10, choices=ATTRIBUTE_MODIFIED_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.is_instant and self.cast_time != 0:
            raise ValidationError("Instant actions must have cast_time = 0.")
        if not self.is_instant and self.cast_time == 0:
            raise ValidationError("cast_time can only be 0 if is_instant is True.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} | {self.type}'
