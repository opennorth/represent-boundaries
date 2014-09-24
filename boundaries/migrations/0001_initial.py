# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Boundary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_name', models.CharField(max_length=100, help_text='A generic singular name for the boundary.')),
                ('slug', models.SlugField(max_length=200, help_text="The boundary's unique identifier within the set, used as a path component in URLs.")),
                ('external_id', models.CharField(max_length=64, help_text='An identifier of the boundary, which should be unique within the set.')),
                ('name', models.CharField(db_index=True, max_length=192, help_text='The name of the boundary.')),
                ('metadata', jsonfield.fields.JSONField(default=dict, help_text='The attributes of the boundary from the shapefile, as a dictionary.', blank=True)),
                ('shape', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, help_text='The geometry of the boundary in EPSG:4326.')),
                ('simple_shape', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, help_text='The simplified geometry of the boundary in EPSG:4326.')),
                ('centroid', django.contrib.gis.db.models.fields.PointField(srid=4326, help_text='The centroid of the boundary in EPSG:4326.', null=True)),
                ('extent', jsonfield.fields.JSONField(blank=True, help_text='The bounding box of the boundary as a list like [xmin, ymin, xmax, ymax] in EPSG:4326.', null=True)),
                ('label_point', django.contrib.gis.db.models.fields.PointField(spatial_index=False, srid=4326, blank=True, help_text='The point at which to place a label for the boundary in EPSG:4326, used by represent-maps.', null=True)),
            ],
            options={
                'verbose_name_plural': 'boundaries',
                'verbose_name': 'boundary',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoundarySet',
            fields=[
                ('slug', models.SlugField(primary_key=True, help_text="The boundary set's unique identifier, used as a path component in URLs.", serialize=False, max_length=200, editable=False)),
                ('name', models.CharField(max_length=100, help_text='The plural name of the boundary set.', unique=True)),
                ('singular', models.CharField(max_length=100, help_text='A generic singular name for a boundary in the set.')),
                ('authority', models.CharField(max_length=256, help_text='The entity responsible for publishing the data.')),
                ('domain', models.CharField(max_length=256, help_text='The geographic area covered by the boundary set.')),
                ('last_updated', models.DateField(help_text='The most recent date on which the data was updated.')),
                ('source_url', models.URLField(help_text='A URL to the source of the data.', blank=True)),
                ('notes', models.TextField(help_text='Free-form text notes, often used to describe changes that were made to the original source data.', blank=True)),
                ('licence_url', models.URLField(help_text='A URL to the licence under which the data is made available.', blank=True)),
                ('extent', jsonfield.fields.JSONField(blank=True, help_text="The set's boundaries' bounding box as a list like [xmin, ymin, xmax, ymax] in EPSG:4326.", null=True)),
                ('start_date', models.DateField(blank=True, help_text="The date from which the set's boundaries are in effect.", null=True)),
                ('end_date', models.DateField(blank=True, help_text="The date until which the set's boundaries are in effect.", null=True)),
                ('extra', jsonfield.fields.JSONField(blank=True, help_text='Any additional metadata.', null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'boundary sets',
                'verbose_name': 'boundary set',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='boundary',
            name='set',
            field=models.ForeignKey(related_name='boundaries', to='boundaries.BoundarySet', help_text='The set to which the boundary belongs.'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='boundary',
            unique_together=set([('slug', 'set')]),
        ),
    ]
