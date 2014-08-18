# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import __builtin__
import jsonfield.fields
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Boundary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('set_name', models.CharField(help_text='Category of boundaries that this boundary belongs, e.g. "Community Areas".', max_length=100)),
                ('slug', models.SlugField(help_text='The name of this BoundarySet used in API URLs.', max_length=200)),
                ('external_id', models.CharField(help_text="The boundary's unique ID in the source dataset, or a generated one.", max_length=64)),
                ('name', models.CharField(help_text='The name of this boundary, e.g. "Austin".', max_length=192, db_index=True)),
                ('metadata', jsonfield.fields.JSONField(default=__builtin__.dict, help_text='The complete contents of the attribute table for this boundary from the source shapefile, structured as JSON.', blank=True)),
                ('shape', django.contrib.gis.db.models.fields.MultiPolygonField(help_text='The geometry of this boundary in EPSG:4326 projection.', srid=4326)),
                ('simple_shape', django.contrib.gis.db.models.fields.MultiPolygonField(help_text='The simplified geometry of this boundary in EPSG:4326 projection.', srid=4326)),
                ('centroid', django.contrib.gis.db.models.fields.PointField(help_text='The centroid (weighted center) of this boundary in EPSG:4326 projection.', srid=4326, null=True)),
                ('extent', jsonfield.fields.JSONField(help_text='The bounding box of the boundary in EPSG:4326 projection, as a list such as [xmin, ymin, xmax, ymax].', null=True, blank=True)),
                ('label_point', django.contrib.gis.db.models.fields.PointField(help_text='The suggested location to label this boundary in EPSG:4326 projection. Used by represent-maps, but not actually used within represent-boundaries.', srid=4326, null=True, spatial_index=False, blank=True)),
            ],
            options={
                'verbose_name': 'boundary',
                'verbose_name_plural': 'boundaries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoundarySet',
            fields=[
                ('slug', models.SlugField(primary_key=True, serialize=False, editable=False, max_length=200, help_text='The name of this BoundarySet used in API URLs.')),
                ('name', models.CharField(help_text='Category of boundaries, e.g. "Community Areas".', unique=True, max_length=100)),
                ('singular', models.CharField(help_text='Name of a single boundary, e.g. "Community Area".', max_length=100)),
                ('authority', models.CharField(help_text='The entity responsible for this data\'s accuracy, e.g. "City of Chicago".', max_length=256)),
                ('domain', models.CharField(help_text='The area that this BoundarySet covers, e.g. "Chicago" or "Illinois".', max_length=256)),
                ('last_updated', models.DateField(help_text='The last time this data was updated from its authority (but not necessarily the date it is current as of).')),
                ('source_url', models.URLField(help_text='The url this data was found at, if any.', blank=True)),
                ('notes', models.TextField(help_text='Notes about loading this data, including any transformations that were applied to it.', blank=True)),
                ('licence_url', models.URLField(help_text='The URL to the text of the licence this data is distributed under.', blank=True)),
                ('extent', jsonfield.fields.JSONField(help_text='The bounding box of the boundaries in EPSG:4326 projection, as a list such as [xmin, ymin, xmax, ymax].', null=True, blank=True)),
                ('start_date', models.DateField(help_text='The date on which this set of boundaries went into effect.', null=True, blank=True)),
                ('end_date', models.DateField(help_text='The date on which this set of boundaries was superceded.', null=True, blank=True)),
                ('extra', jsonfield.fields.JSONField(help_text='Any other nonstandard metadata provided when creating this boundary set.', null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'boundary set',
                'verbose_name_plural': 'boundary sets',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='boundary',
            name='set',
            field=models.ForeignKey(help_text='Category of boundaries that this boundary belongs, e.g. "Community Areas".', to='boundaries.BoundarySet'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='boundary',
            unique_together=set([('slug', 'set')]),
        ),
    ]
