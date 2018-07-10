from django.db import models


class Baz(models.Model):

    foo = models.OneToOneField('Foo', models.CASCADE, related_name='baz')
    bars = models.ManyToManyField('Bar', related_name='bazs')
    file = models.FileField(blank=True, null=True)
