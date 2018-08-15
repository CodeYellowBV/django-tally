from django.db import models
from django.contrib.postgres import fields as pg_fields


class Data(models.Model):
    """
    Saves tally data on behalf of the DBStored mixin.
    """

    name = models.TextField(primary_key=True)
    value = pg_fields.JSONField(blank=True, null=True)
