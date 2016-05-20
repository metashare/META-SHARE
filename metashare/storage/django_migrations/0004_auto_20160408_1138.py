# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0003_auto_20160407_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storageobject',
            name='modified',
            field=models.DateTimeField(help_text=b'(Read-only) last modification date of the metadata XML for this storage object instance.', auto_now=True),
            preserve_default=True,
        ),
    ]
