from collections import defaultdict
from copy import deepcopy

from django.db import models
from django.core.exceptions import FieldDoesNotExist

from .lang import KW


class InstanceWrapper(defaultdict):

    def __init__(self, instance):
        self._instance = deepcopy(instance)
        self[KW('__class__')] = type(instance).__name__

    def __missing__(self, key):
        if isinstance(key, KW):
            try:
                field = self._instance._meta.get_field(key.value)
            except FieldDoesNotExist:
                pass
            else:
                value = getattr(self._instance, key.value)
                if field.one_to_many or field.many_to_many:
                    value = list(map(InstanceWrapper, value.all()))
                elif isinstance(field, models.ForeignKey):
                    value = InstanceWrapper(value)
                elif isinstance(field, models.FileField):
                    value = value.name
                return value

        return super().__missing__(key)
