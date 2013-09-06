# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'BoundarySet.extra_metadata'
        db.add_column(u'boundaries_boundaryset', 'extra_metadata', self.gf('jsonfield.fields.JSONField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'BoundarySet.extra_metadata'
        db.delete_column(u'boundaries_boundaryset', 'extra_metadata')


    models = {
        u'boundaries.boundary': {
            'Meta': {'unique_together': "(('slug', 'set'),)", 'object_name': 'Boundary'},
            'centroid': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'extent': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label_point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'spatial_index': 'False', 'blank': 'True'}),
            'metadata': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '192', 'db_index': 'True'}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'boundaries'", 'to': u"orm['boundaries.BoundarySet']"}),
            'set_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shape': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'simple_shape': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'db_index': 'True'})
        },
        u'boundaries.boundaryset': {
            'Meta': {'ordering': "('name',)", 'object_name': 'BoundarySet'},
            'authority': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'extent': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'extra_metadata': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateField', [], {}),
            'licence_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'singular': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'primary_key': 'True', 'db_index': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['boundaries']
