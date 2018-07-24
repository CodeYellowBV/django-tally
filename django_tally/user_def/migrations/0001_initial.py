# Generated by Django 2.0.7 on 2018-07-24 04:55

from django.db import migrations, models
import django_tally.data.db_stored
import django_tally.filter
import django_tally.group
import django_tally.tally


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserDefGroupTally',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base', models.TextField(default='null')),
                ('get_tally_body', models.TextField()),
                ('get_value_body', models.TextField(default='"k:instance"')),
                ('handle_change_body', models.TextField()),
                ('filter_value_body', models.TextField(default='true')),
                ('get_group_body', models.TextField()),
                ('db_name', models.TextField(unique=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(django_tally.data.db_stored.DBStored, django_tally.group.Group, django_tally.filter.Filter, django_tally.tally.Tally, models.Model),
        ),
        migrations.CreateModel(
            name='UserDefTally',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base', models.TextField(default='null')),
                ('get_tally_body', models.TextField()),
                ('get_value_body', models.TextField(default='"k:instance"')),
                ('handle_change_body', models.TextField()),
                ('filter_value_body', models.TextField(default='true')),
                ('db_name', models.TextField(unique=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(django_tally.data.db_stored.DBStored, django_tally.filter.Filter, django_tally.tally.Tally, models.Model),
        ),
    ]
