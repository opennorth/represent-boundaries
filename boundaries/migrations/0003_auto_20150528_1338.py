# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0002_auto_20141129_1402'),
    ]

    operations = [
        migrations.AddField(
            model_name='boundary',
            name='end_date',
            field=models.DateField(help_text='The date until which the boundary is in effect.', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boundary',
            name='start_date',
            field=models.DateField(help_text='The date from which the boundary is in effect.', blank=True, null=True),
            preserve_default=True,
        ),
    ]
