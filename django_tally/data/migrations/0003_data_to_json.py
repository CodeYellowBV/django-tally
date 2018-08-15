import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_simplify_data'),
    ]

    operations = [
        migrations.RunSQL(
            (
                'ALTER TABLE data_data '
                'ALTER COLUMN value DROP NOT NULL;'
                'ALTER TABLE data_data '
                'ALTER COLUMN value TYPE JSONB '
                'USING value::JSONB;'
            ),
            (
                'ALTER TABLE data_data '
                'ALTER COLUMN value TYPE TEXT '
                'USING value::TEXT;'
                'ALTER TABLE data_data '
                'ALTER COLUMN value SET NOT NULL;'
            ),
            state_operations=[
                migrations.AlterField(
                    model_name='data',
                    name='value',
                    field=django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, null=True
                    ),
                ),
            ],
        ),
    ]
