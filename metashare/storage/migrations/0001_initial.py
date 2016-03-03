# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StorageObject'
        db.create_table('storage_storageobject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source_url', self.gf('django.db.models.fields.URLField')(default='http://127.0.0.1:8000', max_length=200)),
            ('identifier', self.gf('django.db.models.fields.CharField')(default='afed27dacc1111e5805af04da2da8af840c465a629044fb6b8da193cc20b332b', unique=True, max_length=64)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2016, 2, 5, 0, 0))),
            ('checksum', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('digest_checksum', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('digest_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('digest_last_checked', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('revision', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('metashare_version', self.gf('django.db.models.fields.CharField')(default='3.0', max_length=32)),
            ('copy_status', self.gf('django.db.models.fields.CharField')(default='m', max_length=1)),
            ('publication_status', self.gf('django.db.models.fields.CharField')(default='i', max_length=1)),
            ('source_node', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('metadata', self.gf('django.db.models.fields.TextField')()),
            ('global_storage', self.gf('django.db.models.fields.TextField')(default='not set yet')),
            ('local_storage', self.gf('django.db.models.fields.TextField')(default='not set yet')),
        ))
        db.send_create_signal('storage', ['StorageObject'])


    def backwards(self, orm):
        # Deleting model 'StorageObject'
        db.delete_table('storage_storageobject')


    models = {
        'storage.storageobject': {
            'Meta': {'object_name': 'StorageObject'},
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'copy_status': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'digest_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'digest_last_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'digest_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'global_storage': ('django.db.models.fields.TextField', [], {'default': "'not set yet'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'aff320a4cc1111e5805af04da2da8af809c3dbcf1df14f5a906b243c19e14f2b'", 'unique': 'True', 'max_length': '64'}),
            'local_storage': ('django.db.models.fields.TextField', [], {'default': "'not set yet'"}),
            'metadata': ('django.db.models.fields.TextField', [], {}),
            'metashare_version': ('django.db.models.fields.CharField', [], {'default': "'3.0'", 'max_length': '32'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2016, 2, 5, 0, 0)'}),
            'publication_status': ('django.db.models.fields.CharField', [], {'default': "'i'", 'max_length': '1'}),
            'revision': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'source_node': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'default': "'http://127.0.0.1:8000'", 'max_length': '200'})
        }
    }

    complete_apps = ['storage']