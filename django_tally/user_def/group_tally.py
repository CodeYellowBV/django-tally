from django.db import models

from ..data import DBStored
from ..group import Group
from .tally import UserDefTallyBaseNonStored, UserDefTallyBaseNonFiltered
from .lang import json


class UserDefGroupTallyBaseNonStored(Group, UserDefTallyBaseNonStored):

    get_group_body = models.TextField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._decoded_get_group_body = None

    @property
    def _get_group_body(self):
        if self._decoded_get_group_body is None:
            self._decoded_get_group_body = json.loads(self.get_group_body)
        return self._decoded_get_group_body

    @_get_group_body.setter
    def _get_group_body(self, value):
        self._decoded_get_group_body = value
        self.get_group_body = json.dumps(value)

    def refresh_from_db(self, *args, **kwargs):
        self._decoded_get_group_body = None
        return super().refresh_from_db()

    def get_group(self, value):
        return self.run(self._get_group_body, value=value)

    class Meta:
        abstract = True


class UserDefGroupTallyBase(DBStored, UserDefGroupTallyBaseNonStored):

    db_name = models.TextField(unique=True)

    def __init__(self, *args, **kwargs):
        super(UserDefTallyBaseNonFiltered, self).__init__(None)
        super(DBStored, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True
