# Generated by Django 2.2 on 2020-05-06 20:30

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Download',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(db_index=True, max_length=256)),
                ('ip', models.GenericIPAddressField(blank=True, default='', null=True, verbose_name='آی\u200cپی')),
                ('at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'دانلود',
                'verbose_name_plural': 'دانلودها',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VerificationSms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VerificationGa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=16)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('national_id', models.CharField(default=None, max_length=10, unique=True)),
                ('mobile', models.CharField(default=None, max_length=11, unique=True)),
                ('mobile_verified', models.BooleanField(default=False)),
                ('email_verified', models.BooleanField(default=False)),
                ('fathers_name', models.CharField(default=None, max_length=20)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('birth_place', models.CharField(default=None, max_length=30)),
                ('identity_card_number', models.CharField(default=None, max_length=10)),
                ('home_address', models.TextField(default=None, max_length=120)),
                ('work_address', models.TextField(default=None, max_length=120)),
                ('tel', models.CharField(default=None, max_length=15)),
                ('verification_type', models.IntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('access_token', models.CharField(db_index=True, max_length=60, unique=True)),
                ('refresh_token', models.CharField(max_length=60, primary_key=True, serialize=False)),
                ('access_token_created_at', models.DateTimeField(auto_now=True)),
                ('refresh_token_created_at', models.DateTimeField(auto_now_add=True)),
                ('access_token_lifetime', models.IntegerField(default=10)),
                ('refresh_token_lifetime', models.IntegerField(default=120)),
                ('access_ip', models.GenericIPAddressField(verbose_name='آی\u200cپی')),
                ('agent', models.CharField(default=None, max_length=80)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'توکن',
                'verbose_name_plural': 'توکن\u200cها',
            },
        ),
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('created_ip', models.GenericIPAddressField(blank=True, default='', editable=False, null=True, verbose_name='آی\u200cپی سازنده')),
                ('updated_ip', models.GenericIPAddressField(blank=True, default='', editable=False, null=True, verbose_name='آی\u200cپی ادیتور')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_preferences_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_preferences_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'تنظیم',
                'verbose_name_plural': 'تنظیمات',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MobileTemp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('created_ip', models.GenericIPAddressField(blank=True, default='', editable=False, null=True, verbose_name='آی\u200cپی سازنده')),
                ('updated_ip', models.GenericIPAddressField(blank=True, default='', editable=False, null=True, verbose_name='آی\u200cپی ادیتور')),
                ('number', models.CharField(max_length=20, unique=True, verbose_name='شماره')),
                ('ip', models.GenericIPAddressField(verbose_name='آی\u200cپی')),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_mobiletemp_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_mobiletemp_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'شماره بالقوه',
                'verbose_name_plural': 'شماره\u200cهای بالقوه',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, default='', max_length=100)),
                ('body', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('ctype', models.IntegerField(choices=[(1, 'SMS'), (2, 'Email')], default=1)),
                ('status', models.IntegerField(choices=[(0, 'New'), (1, 'Inprogress'), (2, 'Retry'), (9, 'Failed'), (10, 'Done')], default=0)),
                ('target', models.CharField(max_length=50)),
                ('target_group', models.IntegerField(blank=True, null=True)),
                ('start_at', models.DateTimeField(blank=True, null=True)),
                ('stop_at', models.DateTimeField(blank=True, null=True)),
                ('index', models.CharField(default='', max_length=20)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('gtw', models.IntegerField(choices=[(0, 'unknown gateway'), (1, 'django send mail'), (11, 'parsa sms'), (12, 'parsa template sms')], default=0)),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=60)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'role')},
            },
        ),
        migrations.CreateModel(
            name='Confirm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('created_ip', models.GenericIPAddressField(blank=True, default='', editable=False, null=True, verbose_name='آی\u200cپی سازنده')),
                ('updated_ip', models.GenericIPAddressField(blank=True, default='', editable=False, null=True, verbose_name='آی\u200cپی ادیتور')),
                ('which', models.IntegerField(choices=[(1, 'Email'), (2, 'Mobile'), (10, 'Reset Password')], default=2)),
                ('code', models.CharField(max_length=36)),
                ('count', models.IntegerField(default=1)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_confirm_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='core_confirm_updated_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'تأیید',
                'verbose_name_plural': 'تأییدات',
                'abstract': False,
                'unique_together': {('user', 'which')},
            },
        ),
    ]
