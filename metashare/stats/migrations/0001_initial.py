# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LRStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lrid', models.CharField(max_length=64)),
                ('userid', models.CharField(max_length=64)),
                ('geoinfo', models.CharField(max_length=2, blank=True)),
                ('sessid', models.CharField(max_length=64)),
                ('lasttime', models.DateTimeField()),
                ('action', models.CharField(max_length=1)),
                ('count', models.IntegerField(default=1)),
                ('ignored', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='QueryStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('userid', models.CharField(max_length=64)),
                ('geoinfo', models.CharField(max_length=2, blank=True)),
                ('query', models.TextField()),
                ('facets', models.TextField()),
                ('lasttime', models.DateTimeField()),
                ('found', models.IntegerField(default=0)),
                ('exectime', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='UsageStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lrid', models.CharField(max_length=64)),
                ('elname', models.CharField(max_length=64)),
                ('elparent', models.CharField(max_length=64, blank=True)),
                ('text', models.TextField(blank=True)),
                ('count', models.IntegerField(default=1)),
            ],
        ),
    ]
