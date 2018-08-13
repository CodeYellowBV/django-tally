from django.db import models

from ..data import DBStored
from ..group import Group
from .tally import UserDefTallyBaseNonStored
from .lang import json, run, Env


class UserDefGroupTallyBaseNonStored(UserDefTallyBaseNonStored):

    get_group = models.TextField()

    def as_tally(self, **kwargs):
        return super().as_tally(get_group=json.loads(self.get_group), **kwargs)

    class UserTally(Group, UserDefTallyBaseNonStored.UserTally):

        def __init__(self, get_group=None, **kwargs):
            super(Group, self).__init__(**kwargs)
            self._get_group = get_group

        def get_group(self, value):
            return run(self._get_group, Env(base_env=self._env, value=value))

    class Meta:
        abstract = True


class UserDefGroupTallyBase(UserDefGroupTallyBaseNonStored):

    db_name = models.TextField(unique=True)

    def as_tally(self):
        return super().as_tally(db_name=self.db_name)

    class UserTally(DBStored, UserDefGroupTallyBaseNonStored.UserTally):

        def __init__(self, db_name=None, **kwargs):
            super(DBStored, self).__init__(**kwargs)
            self.db_name = db_name
            self.ensure_data()

    class Meta:
        abstract = True
