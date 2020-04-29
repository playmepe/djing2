# Generated by Django 2.2.9 on 2020-04-26 20:33

from django.db import migrations, models

from djing2.lib.for_migrations import read_all_file


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0004_networkippool_is_dynamic'),
    ]

    operations = [
        migrations.AddField(
            model_name='networkippool',
            name='pool_tag',
            field=models.CharField(blank=True, default=None, max_length=32, null=True, verbose_name='Tag'),
        ),
        migrations.RunSQL(
            sql=read_all_file('0005_networkippool_tag.sql', __file__)
        )
    ]