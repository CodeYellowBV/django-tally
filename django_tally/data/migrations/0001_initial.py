# Generated by Django 2.0.7 on 2018-07-24 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('name', models.TextField(primary_key=True, serialize=False)),
                ('value', models.BinaryField()),
            ],
        ),
    ]
