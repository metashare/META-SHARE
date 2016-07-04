# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceCountDict',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lrid', models.CharField(max_length=64, editable=False, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='ResourceCountPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lrid', models.CharField(max_length=64, editable=False, db_index=True)),
                ('count', models.PositiveIntegerField(default=0)),
                ('container', models.ForeignKey(to='recommendations.ResourceCountDict')),
            ],
        ),
        migrations.CreateModel(
            name='TogetherManager',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='resourcecountdict',
            name='container',
            field=models.ForeignKey(to='recommendations.TogetherManager'),
        ),
        migrations.AlterUniqueTogether(
            name='resourcecountpair',
            unique_together=set([('container', 'lrid')]),
        ),
    ]
