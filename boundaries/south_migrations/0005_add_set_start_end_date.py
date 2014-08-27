# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BoundarySet.start_date'
        db.add_column(u'boundaries_boundaryset', 'start_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'BoundarySet.end_date'
        db.add_column(u'boundaries_boundaryset', 'end_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'BoundarySet.start_date'
        db.delete_column(u'boundaries_boundaryset', 'start_date')

        # Deleting field 'BoundarySet.end_date'
        db.delete_column(u'boundaries_boundaryset', 'end_date')

    models = {
        u'boundaries.boundary': {
            'Meta': {'unique_together': "((u'slug', u'set'),)", 'object_name': 'Boundary'},
            'centroid': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'extent': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label_point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'spatial_index': 'False', 'blank': 'True'}),
            'metadata': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '192', 'db_index': 'True'}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'boundaries'", 'to': u"orm['boundaries.BoundarySet']"}),
            'set_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shape': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'simple_shape': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200'})
        },
        u'boundaries.boundaryset': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'BoundarySet'},
            'authority': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'extent': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'extra': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateField', [], {}),
            'licence_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'singular': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'primary_key': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['boundaries']
