# Generated by Django 2.2 on 2020-05-08 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20200508_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermeta',
            name='fathers_name',
            field=models.CharField(blank=True, default=None, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='usermeta',
            name='home_address',
            field=models.TextField(blank=True, default=None, max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='usermeta',
            name='identity_card_number',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='usermeta',
            name='national_id',
            field=models.CharField(blank=True, default=None, max_length=10, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='usermeta',
            name='tel',
            field=models.CharField(blank=True, default=None, max_length=15, null=True),
        ),
    ]