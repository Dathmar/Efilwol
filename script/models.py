from django.db import models

# Create your models here.
class Script(models.Model):
    ROLE_CHOICES = [
        ('tank', 'Tank'),
        ('dps', 'DPS'),
    ]

    DAMAGE_RANGE_CHOICES = [
        ('melee', 'Melee'),
        ('ranged', 'Ranged'),
    ]

    DAMAGE_SPECIALIZATION_CHOICES = [
        ('physical', 'Physical'),
        ('lightning', 'Lightning'),
        ('fire', 'Fire'),
        ('ice', 'Ice'),
        ('earth', 'Earth'),
        ('water', 'Water'),
        ('poison', 'Poison'),
        ('necrotic', 'Necrotic'),

        ('none', 'None'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    damage_range = models.CharField(max_length=10, choices=DAMAGE_RANGE_CHOICES)
    damage_specialization = models.CharField(max_length=20, choices=DAMAGE_SPECIALIZATION_CHOICES)
    health = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} | {self.role} | {self.damage_range} | {self.damage_specialization}'


class Spell(models.Model):
    TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('lightning', 'Lightning'),
        ('fire', 'Fire'),
        ('ice', 'Ice'),
        ('earth', 'Earth'),
        ('water', 'Water'),
        ('poison', 'Poison'),
        ('necrotic', 'Necrotic'),

        ('healing', 'Healing'),
        ('buff', 'Buff'),
        ('debuff', 'Debuff'),
    ]

    SCOPE_CHOICES = [
        ('single', 'Single'),
        ('multiple', 'Multiple'),
        ('party', 'Party'),
    ]

    ATTRIBUTE_MODIFIED_CHOICES = [
        ('health', 'Health'),
        ('mana', 'Mana'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()

    modifier = models.IntegerField(
        help_text="Numerical scaling factor for this spell e.g. the damage or healing done. "
                  "But can also be the strength of a buff",
        default=0
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='physical')
    mana_cost = models.IntegerField()
    cooldown = models.IntegerField()
    duration = models.IntegerField(
        help_text="Duration of the spell in seconds.  For damage or healing this will be the hot/dot time",
        null=True, blank=True)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, default='single')
    attribute_modified = models.CharField(max_length=10, choices=ATTRIBUTE_MODIFIED_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} | {self.type}'
