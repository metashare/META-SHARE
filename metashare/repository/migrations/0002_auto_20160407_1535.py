# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationinfotype_model',
            name='back_to_resourceinfotype_model',
            field=models.ForeignKey(related_name='relationinfotype_model_set', blank=True, to='repository.resourceInfoType_model', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sizeinfotype_model',
            name='back_to_audiosizeinfotype_model',
            field=models.ForeignKey(related_name='sizeinfotype_model_set', blank=True, to='repository.audioSizeInfoType_model', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='validationinfotype_model',
            name='back_to_resourceinfotype_model',
            field=models.ForeignKey(related_name='validationinfotype_model_set', blank=True, to='repository.resourceInfoType_model', null=True),
            preserve_default=True,
        ),
    ]
