# Generated by Django 2.2.10 on 2020-03-30 16:15

from django.db import migrations
from djing2.lib.for_migrations import read_all_file


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=read_all_file('0003_add_procedures.sql', __file__),
            reverse_sql="DROP FUNCTION IF EXISTS find_customer_service_by_ip( inet );"
        )
    ]