# Generated by Django 2.1.7 on 2019-02-20 00:12

import bitfield.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('groupapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(max_length=127, unique=True, validators=[django.core.validators.RegexValidator('^\\w{1,127}$')], verbose_name='profile username')),
                ('fio', models.CharField(max_length=256, verbose_name='fio')),
                ('birth_day', models.DateField(auto_now_add=True, verbose_name='birth day')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('is_admin', models.BooleanField(default=False)),
                ('telephone', models.CharField(blank=True, max_length=16, validators=[django.core.validators.RegexValidator('^(\\+[7,8,9,3]\\d{10,11})?$')], verbose_name='Telephone')),
            ],
            options={
                'db_table': 'base_accounts',
                'ordering': ('username',),
            },
        ),
        migrations.CreateModel(
            name='UserProfileLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta_info', jsonfield.fields.JSONField(verbose_name='Meta information')),
                ('do_type', models.CharField(choices=[('cusr', 'Create user'), ('dusr', 'Delete user'), ('cdev', 'Create device'), ('ddev', 'Delete device'), ('cnas', 'Create NAS'), ('dnas', 'Delete NAS'), ('csrv', 'Create service'), ('dsrv', 'Delete service')], max_length=4, verbose_name='Action type')),
                ('additional_text', models.CharField(blank=True, max_length=512, null=True, verbose_name='Additional info')),
                ('action_date', models.DateTimeField(auto_now_add=True, verbose_name='Action date')),
            ],
            options={
                'verbose_name': 'User profile log',
                'verbose_name_plural': 'User profile logs',
                'ordering': ('-action_date',),
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('baseaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='profiles.BaseAccount')),
                ('avatar', models.ImageField(blank=True, default=None, null=True, upload_to='user/avatar', verbose_name='Avatar')),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('flags', bitfield.models.BitField((('notify_task', 'Notification about tasks'), ('notify_msg', 'Notification about messages'), ('notify_mon', 'Notification from monitoring')), default=0, verbose_name='Settings flags')),
                ('responsibility_groups', models.ManyToManyField(blank=True, to='groupapp.Group', verbose_name='Responsibility groups')),
            ],
            options={
                'verbose_name': 'Staff account profile',
                'verbose_name_plural': 'Staff account profiles',
                'ordering': ('fio',),
            },
            bases=('profiles.baseaccount',),
        ),
        migrations.AddField(
            model_name='userprofilelog',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Author'),
        ),
        migrations.AddField(
            model_name='baseaccount',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='baseaccount',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
