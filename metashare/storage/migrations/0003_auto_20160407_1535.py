# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_auto_20160301_1604'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storageobject',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 7, 15, 35, 31, 661839), help_text=b'(Read-only) last modification date of the metadata XML for this storage object instance.', editable=False),
            preserve_default=True,
        ),
    ]
