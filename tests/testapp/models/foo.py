from django.db import models


class Foo(models.Model):

    value = models.IntegerField(default=1)
