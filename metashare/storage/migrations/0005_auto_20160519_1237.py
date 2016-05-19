# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0004_auto_20160408_1138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storageobject',
            name='metashare_version',
            field=models.CharField(default=b'3.1', help_text=b'(Read-only) META-SHARE version used with the storage object instance.', max_length=32, editable=False),
            preserve_default=True,
        ),
    ]
