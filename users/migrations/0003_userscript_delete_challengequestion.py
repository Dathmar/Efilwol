# Generated by Django 5.1.3 on 2024-12-11 19:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('script', '0004_remove_spell_damage_remove_spell_damage_type_and_more'),
        ('users', '0002_challengequestion'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserScript',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('in_party', models.BooleanField(default=False)),
                ('script', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='script.script')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='ChallengeQuestion',
        ),
    ]
