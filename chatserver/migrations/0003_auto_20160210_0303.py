# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('chatserver', '0002_auto_20160209_2007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tictacgamesession',
            name='user',
            field=models.ForeignKey(related_name='player', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tictacgamesession',
            name='user2',
            field=models.ForeignKey(related_name='player2', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
