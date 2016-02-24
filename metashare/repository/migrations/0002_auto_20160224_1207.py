# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationinfotype_model',
            name='back_to_resourceinfotype_model',
            field=models.ForeignKey(related_name='relation_info_type', blank=True, to='repository.resourceInfoType_model', null=True),
        ),
        migrations.AlterField(
            model_name='validationinfotype_model',
            name='back_to_resourceinfotype_model',
            field=models.ForeignKey(related_name='validation_info_type', blank=True, to='repository.resourceInfoType_model', null=True),
        ),
    ]
