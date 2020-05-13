# Generated by Django 2.2 on 2020-05-09 19:29

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20200508_1756'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermeta',
            name='identity_card_image',
            field=models.ImageField(blank=True, null=True, upload_to=core.models.upload_to_photo),
        ),
        migrations.AddField(
            model_name='usermeta',
            name='national_card_image',
            field=models.ImageField(blank=True, null=True, upload_to=core.models.upload_to_photo),
        ),
    ]