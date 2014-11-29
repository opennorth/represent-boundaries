# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


def set_defaults(apps, schema_editor):
    Boundary = apps.get_model("boundaries", "Boundary")
    for boundary in Boundary.objects.all():
        if boundary.metadata is None:
            boundary.metadata = {}
        boundary.save()


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_defaults),
        migrations.AlterField(
            model_name='boundary',
            name='metadata',
            field=jsonfield.fields.JSONField(default={}, help_text='The attributes of the boundary from the shapefile, as a dictionary.'),
        ),
        migrations.AlterField(
            model_name='boundaryset',
            name='extra',
            field=jsonfield.fields.JSONField(default={}, help_text='Any additional metadata.'),
        ),
    ]
