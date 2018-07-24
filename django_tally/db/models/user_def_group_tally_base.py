from django.db import models

from ..db_stored import DBStored
from ...group import Group
from .user_def_tally_base import get_user_def_tally_base
from ..lang import json


def get_user_def_group_tally_base(base_class=models.Model):
    """
    Creates a user def group tally base class for a certain base class.

    @param base_class: Class
        The base class to base the returned class on. Defaults to
        django.db.models.Model.
    @return: Class
        The generated base class.
    """

    (
        UserDefTallyBaseNonFiltered,
        UserDefTallyBaseNonStored,
        UserDefTallyBase,
    ) = get_user_def_tally_base(base_class, return_all=True)

    class UserDefGroupTallyBaseNonStored(Group, UserDefTallyBaseNonStored):

        _get_group_body = models.BinaryField()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._decoded_get_group_body = None

        @property
        def get_group_body(self):
            if self._decoded_get_group_body is None:
                self._decoded_get_group_body = json.loads(
                    self._get_group_body.decode()
                )
            return self._decoded_get_group_body

        @get_group_body.setter
        def get_group_body(self, value):
            self._decoded_get_group_body = value
            self._get_group_body = json.dumps(value).encode()

        def refresh_from_db(self, *args, **kwargs):
            self._decoded_get_group_body = None
            return super().refresh_from_db()

        def get_group(self, value):
            return self.run(self.get_group_body, value=value)

        class Meta:
            abstract = True

    class UserDefGroupTallyBase(DBStored, UserDefGroupTallyBaseNonStored):

        db_name = models.TextField(unique=True)

        def __init__(self, *args, **kwargs):
            super(UserDefTallyBaseNonFiltered, self).__init__(None)
            super(DBStored, self).__init__(*args, **kwargs)

        class Meta:
            abstract = True

    return UserDefGroupTallyBase


UserDefGroupTallyBase = get_user_def_group_tally_base()
