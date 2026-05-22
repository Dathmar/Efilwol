from django.db import migrations, models


def set_is_instant_for_zero_cast_time(apps, schema_editor):
    """Data migration: set is_instant=True for all actions with cast_time=0."""
    Action = apps.get_model('script', 'Action')
    Action.objects.filter(cast_time=0).update(is_instant=True)


class Migration(migrations.Migration):

    dependencies = [
        ('script', '0008_rename_health_npcscript_hp_rename_health_script_hp'),
    ]

    operations = [
        # Step 1: Add is_instant as nullable (so existing rows don't violate NOT NULL)
        migrations.AddField(
            model_name='action',
            name='is_instant',
            field=models.BooleanField(
                default=False,
                null=True,
                help_text='If True, this action fires instantly (cast_time must be 0).',
            ),
        ),
        # Step 2: Data migration — set is_instant=True where cast_time=0
        migrations.RunPython(
            set_is_instant_for_zero_cast_time,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 3: Make is_instant non-nullable with default=False
        migrations.AlterField(
            model_name='action',
            name='is_instant',
            field=models.BooleanField(
                default=False,
                help_text='If True, this action fires instantly (cast_time must be 0).',
            ),
        ),
    ]
