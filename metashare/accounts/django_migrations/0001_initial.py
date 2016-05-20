# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import metashare.accounts.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EditorGroup',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
            ],
            options={
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='EditorGroupApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('editor_group', models.OneToOneField(to='accounts.EditorGroup')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EditorGroupManagers',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
                ('managed_group', models.OneToOneField(to='accounts.EditorGroup')),
            ],
            options={
                'verbose_name': 'editor group managers group',
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
            ],
            options={
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='OrganizationApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('organization', models.OneToOneField(to='accounts.Organization')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationManagers',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
                ('managed_organization', models.OneToOneField(to='accounts.Organization')),
            ],
            options={
                'verbose_name': 'organization managers group',
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='RegistrationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(null=True, blank=True, max_length=32, verbose_name=b'UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResetRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(null=True, blank=True, max_length=32, verbose_name=b'UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('uuid', models.CharField(null=True, blank=True, max_length=32, verbose_name=b'UUID')),
                ('birthdate', models.DateField(null=True, verbose_name=b'Date of birth', blank=True)),
                ('affiliation', models.TextField(verbose_name=b'Affiliation(s)', blank=True)),
                ('position', models.CharField(max_length=50, blank=True)),
                ('homepage', models.URLField(blank=True)),
                ('default_editor_groups', models.ManyToManyField(to='accounts.EditorGroup', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('ms_associate_member', 'Is a META-SHARE associate member.'), ('ms_full_member', 'Is a META-SHARE full member.')),
            },
            bases=(models.Model,),
        ),
    ]
