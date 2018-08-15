from django.contrib.postgres.fields.jsonb import JSONField
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_def', '0003_userdeftemplate'),
    ]

    operations = [
        migrations.RunSQL(
            (
                'ALTER TABLE userdef_{model} '
                'ALTER COLUMN {field} DROP NOT NULL;'
                'ALTER TABLE userdef_{model} '
                'ALTER COLUMN {field} TYPE JSONB '
                'USING {field}::JSONB;'
                .format(model=model, field=field)
            ),
            (
                'ALTER TABLE userdef_{model} '
                'ALTER COLUMN {field} TYPE TEXT '
                'USING {field}::TEXT;'
                'ALTER TABLE userdef_{model} '
                'ALTER COLUMN {field} DROP NOT NULL;'
                .format(model=model, field=field)
            ),
            state_operations=[
                migrations.AlterField(
                    model_name=model,
                    name=field,
                    field=JSONField(default=default, blank=True, null=True),
                ),
            ]
        )
        for model, field, default in [
            ('userdefgrouptally', 'base', None),
            ('userdefgrouptally', 'filter_value', True),
            ('userdefgrouptally', 'get_group', None),
            ('userdefgrouptally', 'get_nonexisting_value', None),
            ('userdefgrouptally', 'get_tally', None),
            ('userdefgrouptally', 'get_value', "k:instance"),
            ('userdefgrouptally', 'handle_change', None),
            ('userdeftally', 'base', None),
            ('userdeftally', 'filter_value', True),
            ('userdeftally', 'get_nonexisting_value', None),
            ('userdeftally', 'get_tally', None),
            ('userdeftally', 'get_value', "k:instance"),
            ('userdeftally', 'handle_change', None),
            ('userdeftemplate', 'template', None),
        ]
    ] + [
        migrations.RunSQL(
            (
                'ALTER TABLE userdef_userdeftemplate '
                'ALTER COLUMN params TYPE JSONB '
                'USING params::JSONB;'
            ),
            (
                'ALTER TABLE userdef_userdeftemplate '
                'ALTER COLUMN params TYPE TEXT '
                'USING params::TEXT;'
            ),
            state_operations=[
                migrations.AlterField(
                    model_name='userdeftemplate',
                    name='params',
                    field=JSONField(default=dict, blank=True),
                ),
            ]
        )
    ]
