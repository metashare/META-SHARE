# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TogetherManager'
        db.create_table('recommendations_togethermanager', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('recommendations', ['TogetherManager'])

        # Adding model 'ResourceCountDict'
        db.create_table('recommendations_resourcecountdict', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('container', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['recommendations.TogetherManager'])),
            ('lrid', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
        ))
        db.send_create_signal('recommendations', ['ResourceCountDict'])

        # Adding model 'ResourceCountPair'
        db.create_table('recommendations_resourcecountpair', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('container', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['recommendations.ResourceCountDict'])),
            ('lrid', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('recommendations', ['ResourceCountPair'])

        # Adding unique constraint on 'ResourceCountPair', fields ['container', 'lrid']
        db.create_unique('recommendations_resourcecountpair', ['container_id', 'lrid'])


    def backwards(self, orm):
        # Removing unique constraint on 'ResourceCountPair', fields ['container', 'lrid']
        db.delete_unique('recommendations_resourcecountpair', ['container_id', 'lrid'])

        # Deleting model 'TogetherManager'
        db.delete_table('recommendations_togethermanager')

        # Deleting model 'ResourceCountDict'
        db.delete_table('recommendations_resourcecountdict')

        # Deleting model 'ResourceCountPair'
        db.delete_table('recommendations_resourcecountpair')


    models = {
        'recommendations.resourcecountdict': {
            'Meta': {'object_name': 'ResourceCountDict'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recommendations.TogetherManager']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lrid': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'})
        },
        'recommendations.resourcecountpair': {
            'Meta': {'unique_together': "(('container', 'lrid'),)", 'object_name': 'ResourceCountPair'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recommendations.ResourceCountDict']"}),
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lrid': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'})
        },
        'recommendations.togethermanager': {
            'Meta': {'object_name': 'TogetherManager'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['recommendations']