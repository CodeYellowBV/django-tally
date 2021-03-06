# Generated by Django 2.0.7 on 2018-07-30 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_def', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdefgrouptally',
            old_name='filter_value_body',
            new_name='filter_value',
        ),
        migrations.RenameField(
            model_name='userdefgrouptally',
            old_name='get_group_body',
            new_name='get_group',
        ),
        migrations.RenameField(
            model_name='userdefgrouptally',
            old_name='get_tally_body',
            new_name='get_tally',
        ),
        migrations.RenameField(
            model_name='userdefgrouptally',
            old_name='get_value_body',
            new_name='get_value',
        ),
        migrations.RenameField(
            model_name='userdefgrouptally',
            old_name='handle_change_body',
            new_name='handle_change',
        ),
        migrations.RenameField(
            model_name='userdeftally',
            old_name='filter_value_body',
            new_name='filter_value',
        ),
        migrations.RenameField(
            model_name='userdeftally',
            old_name='get_tally_body',
            new_name='get_tally',
        ),
        migrations.RenameField(
            model_name='userdeftally',
            old_name='get_value_body',
            new_name='get_value',
        ),
        migrations.RenameField(
            model_name='userdeftally',
            old_name='handle_change_body',
            new_name='handle_change',
        ),
        migrations.AddField(
            model_name='userdefgrouptally',
            name='get_nonexisting_value',
            field=models.TextField(default='null'),
        ),
        migrations.AddField(
            model_name='userdeftally',
            name='get_nonexisting_value',
            field=models.TextField(default='null'),
        ),
    ]
