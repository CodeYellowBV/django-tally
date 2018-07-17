from django.db import models


class Baz(models.Model):

    foo = models.ForeignKey('Foo', models.PROTECT, related_name='bazs')
    bars = models.ManyToManyField('Bar', related_name='bazs')
    file = models.FileField(blank=True, null=True)
