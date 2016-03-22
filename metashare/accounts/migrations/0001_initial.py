# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RegistrationRequest'
        db.create_table('accounts_registrationrequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='bef8f484cc1111e5bb48f04da2da8af8', max_length=32)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['RegistrationRequest'])

        # Adding model 'ResetRequest'
        db.create_table('accounts_resetrequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='bef7bf6acc1111e5bb48f04da2da8af8', max_length=32)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['ResetRequest'])

        # Adding model 'EditorGroup'
        db.create_table('accounts_editorgroup', (
            ('group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('accounts', ['EditorGroup'])

        # Adding model 'EditorGroupApplication'
        db.create_table('accounts_editorgroupapplication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('editor_group', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.EditorGroup'], unique=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['EditorGroupApplication'])

        # Adding model 'EditorGroupManagers'
        db.create_table('accounts_editorgroupmanagers', (
            ('group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
            ('managed_group', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.EditorGroup'], unique=True)),
        ))
        db.send_create_signal('accounts', ['EditorGroupManagers'])

        # Adding model 'Organization'
        db.create_table('accounts_organization', (
            ('group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('accounts', ['Organization'])

        # Adding model 'OrganizationApplication'
        db.create_table('accounts_organizationapplication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('organization', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.Organization'], unique=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['OrganizationApplication'])

        # Adding model 'OrganizationManagers'
        db.create_table('accounts_organizationmanagers', (
            ('group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
            ('managed_organization', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.Organization'], unique=True)),
        ))
        db.send_create_signal('accounts', ['OrganizationManagers'])

        # Adding model 'UserProfile'
        db.create_table('accounts_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='bef18474cc1111e5bb48f04da2da8af8', max_length=32)),
            ('birthdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('affiliation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('position', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('homepage', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('accounts', ['UserProfile'])

        # Adding M2M table for field default_editor_groups on 'UserProfile'
        m2m_table_name = db.shorten_name('accounts_userprofile_default_editor_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['accounts.userprofile'], null=False)),
            ('editorgroup', models.ForeignKey(orm['accounts.editorgroup'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userprofile_id', 'editorgroup_id'])


    def backwards(self, orm):
        # Deleting model 'RegistrationRequest'
        db.delete_table('accounts_registrationrequest')

        # Deleting model 'ResetRequest'
        db.delete_table('accounts_resetrequest')

        # Deleting model 'EditorGroup'
        db.delete_table('accounts_editorgroup')

        # Deleting model 'EditorGroupApplication'
        db.delete_table('accounts_editorgroupapplication')

        # Deleting model 'EditorGroupManagers'
        db.delete_table('accounts_editorgroupmanagers')

        # Deleting model 'Organization'
        db.delete_table('accounts_organization')

        # Deleting model 'OrganizationApplication'
        db.delete_table('accounts_organizationapplication')

        # Deleting model 'OrganizationManagers'
        db.delete_table('accounts_organizationmanagers')

        # Deleting model 'UserProfile'
        db.delete_table('accounts_userprofile')

        # Removing M2M table for field default_editor_groups on 'UserProfile'
        db.delete_table(db.shorten_name('accounts_userprofile_default_editor_groups'))


    models = {
        'accounts.editorgroup': {
            'Meta': {'object_name': 'EditorGroup', '_ormbases': ['auth.Group']},
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        },
        'accounts.editorgroupapplication': {
            'Meta': {'object_name': 'EditorGroupApplication'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'editor_group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.EditorGroup']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'accounts.editorgroupmanagers': {
            'Meta': {'object_name': 'EditorGroupManagers', '_ormbases': ['auth.Group']},
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'managed_group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.EditorGroup']", 'unique': 'True'})
        },
        'accounts.organization': {
            'Meta': {'object_name': 'Organization', '_ormbases': ['auth.Group']},
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        },
        'accounts.organizationapplication': {
            'Meta': {'object_name': 'OrganizationApplication'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.Organization']", 'unique': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'accounts.organizationmanagers': {
            'Meta': {'object_name': 'OrganizationManagers', '_ormbases': ['auth.Group']},
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'managed_organization': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.Organization']", 'unique': 'True'})
        },
        'accounts.registrationrequest': {
            'Meta': {'object_name': 'RegistrationRequest'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'bf001ea8cc1111e5bb48f04da2da8af8'", 'max_length': '32'})
        },
        'accounts.resetrequest': {
            'Meta': {'object_name': 'ResetRequest'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'beff296ccc1111e5bb48f04da2da8af8'", 'max_length': '32'})
        },
        'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'affiliation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'default_editor_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.EditorGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'befdc360cc1111e5bb48f04da2da8af8'", 'max_length': '32'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['accounts']