# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LRStats'
        db.create_table('stats_lrstats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lrid', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('userid', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('geoinfo', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('sessid', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('lasttime', self.gf('django.db.models.fields.DateTimeField')()),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('ignored', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('stats', ['LRStats'])

        # Adding model 'QueryStats'
        db.create_table('stats_querystats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('userid', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('geoinfo', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('query', self.gf('django.db.models.fields.TextField')()),
            ('facets', self.gf('django.db.models.fields.TextField')()),
            ('lasttime', self.gf('django.db.models.fields.DateTimeField')()),
            ('found', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('exectime', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('stats', ['QueryStats'])

        # Adding model 'UsageStats'
        db.create_table('stats_usagestats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lrid', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('elname', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('elparent', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('stats', ['UsageStats'])


    def backwards(self, orm):
        # Deleting model 'LRStats'
        db.delete_table('stats_lrstats')

        # Deleting model 'QueryStats'
        db.delete_table('stats_querystats')

        # Deleting model 'UsageStats'
        db.delete_table('stats_usagestats')


    models = {
        'stats.lrstats': {
            'Meta': {'object_name': 'LRStats'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'geoinfo': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lasttime': ('django.db.models.fields.DateTimeField', [], {}),
            'lrid': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'sessid': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'userid': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'stats.querystats': {
            'Meta': {'object_name': 'QueryStats'},
            'exectime': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'facets': ('django.db.models.fields.TextField', [], {}),
            'found': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'geoinfo': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lasttime': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.TextField', [], {}),
            'userid': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'stats.usagestats': {
            'Meta': {'object_name': 'UsageStats'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'elname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'elparent': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lrid': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['stats']