# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TicTacGameSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=25)),
                ('user', models.ForeignKey(related_name='player', to=settings.AUTH_USER_MODEL, unique=True)),
                ('user2', models.ForeignKey(related_name='player2', null=True, blank=True, to=settings.AUTH_USER_MODEL, unique=True)),
            ],
        ),
    ]
