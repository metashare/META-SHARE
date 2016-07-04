# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storageobject',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 3, 1, 16, 3, 58, 691856), help_text=b'(Read-only) last modification date of the metadata XML for this storage object instance.', editable=False),
            preserve_default=True,
        ),
    ]
