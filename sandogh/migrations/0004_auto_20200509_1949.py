# Generated by Django 2.2 on 2020-05-09 19:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sandogh', '0003_membershiprequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membershiprequest',
            name='lender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sandogh.Lender'),
        ),
    ]