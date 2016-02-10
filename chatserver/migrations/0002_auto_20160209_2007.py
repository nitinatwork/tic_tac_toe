# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatserver', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tictacgamesession',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
