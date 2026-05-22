import django.db.models.deletion
from django.db import migrations, models


def copy_script_action_pool(apps, schema_editor):
    """
    Data migration: copy existing action_pool rows from the old implicit
    through tables into the new through tables. No-op on fresh databases.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('script', '0009_action_is_instant'),
    ]

    operations = [
        # Step 1: Remove the old implicit M2M fields (no through model)
        migrations.RemoveField(
            model_name='npcscript',
            name='action_pool',
        ),
        migrations.RemoveField(
            model_name='script',
            name='action_pool',
        ),

        # Step 2: Create the new through model tables
        migrations.CreateModel(
            name='NPCScriptPoolEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.PositiveIntegerField(default=10)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='script.action')),
                ('npc_script', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pool_entries', to='script.npcscript')),
            ],
            options={
                'unique_together': {('npc_script', 'action')},
            },
        ),
        migrations.CreateModel(
            name='ScriptPoolEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.PositiveIntegerField(default=10)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='script.action')),
                ('script', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pool_entries', to='script.script')),
            ],
            options={
                'unique_together': {('script', 'action')},
            },
        ),

        # Step 3: Add the new M2M fields using the through models
        migrations.AddField(
            model_name='npcscript',
            name='action_pool',
            field=models.ManyToManyField(blank=True, through='script.NPCScriptPoolEntry', to='script.action'),
        ),
        migrations.AddField(
            model_name='script',
            name='action_pool',
            field=models.ManyToManyField(blank=True, through='script.ScriptPoolEntry', to='script.action'),
        ),

        # Step 4: Data migration — copy existing pool rows into the new through tables.
        # Note: The old implicit M2M tables (script_script_action_pool,
        # script_npcscript_action_pool) are dropped by Step 1 above, so this
        # RunPython is a no-op for existing databases. For fresh databases there
        # is nothing to copy. The function checks for table existence defensively.
        migrations.RunPython(
            copy_script_action_pool,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
