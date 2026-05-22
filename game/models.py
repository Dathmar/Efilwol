from django.db import models
from script.models import NPCScript, Script


class Stage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1, help_text="Display/unlock order")
    is_demo = models.BooleanField(
        default=False,
        help_text="Demo stages are accessible without an account"
    )

    # Which NPCs can appear in this stage
    enemy_pool = models.ManyToManyField(
        NPCScript,
        help_text="Pool of enemies to randomly draw from"
    )
    enemy_count = models.PositiveIntegerField(
        default=3,
        help_text="How many enemies to pick from the pool"
    )

    # Party size constraint — applies to all players (demo and authenticated)
    party_size = models.PositiveIntegerField(
        default=5,
        help_text="Number of party members allowed in this stage (excluding Efilwol)"
    )

    # Starter scripts given to anon/demo players (ignored for auth'd users)
    demo_party_pool = models.ManyToManyField(
        Script,
        blank=True,
        related_name='demo_stages',
        help_text="Scripts randomly assigned to anon players in demo mode"
    )

    xp_reward = models.PositiveIntegerField(default=0)
    min_party_level = models.PositiveIntegerField(
        default=1,
        help_text="Minimum average party level required to unlock this stage"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        tag = ' [DEMO]' if self.is_demo else ''
        return f'Stage {self.order}: {self.name}{tag}'

    def get_enemies(self):
        """Return a list of randomly selected enemies from the pool.

        For demo stages, enemies are drawn from the weakest half of the pool
        (sorted by attack) to keep the difficulty accessible for new players.
        No replacement — the same enemy cannot appear twice.
        """
        import random
        pool = list(self.enemy_pool.all())
        if not pool:
            return []

        if self.is_demo:
            # Sort by attack ascending, take the weakest 50% as candidates
            pool.sort(key=lambda npc: float(npc.attack))
            cutoff = max(self.enemy_count, len(pool) // 2)
            pool = pool[:cutoff]

        count = min(self.enemy_count, len(pool))
        return random.sample(pool, k=count)

    def get_demo_party(self):
        """Return party_size randomly selected scripts for anon players."""
        import random
        pool = list(self.demo_party_pool.all())
        count = min(self.party_size, len(pool))
        return random.sample(pool, k=count) if pool else []
