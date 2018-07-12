from django.db import models


class Data(models.Model):
    """
    Saves tally data on behalf of the DBStored mixin.
    """

    name = models.TextField(primary_key=True)
    value = models.BinaryField()
