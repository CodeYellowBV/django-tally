from django.db import models

from ..data import DBStored
from ..tally import Tally

from .lang import run, Env, json, KW


def instance_to_dict(instance):
    res = {KW('__class__'): type(instance).__name__}
    for field in instance._meta.get_fields():
        if not field.concrete or field.many_to_many:
            continue
        if isinstance(field, models.ForeignKey):
            res[KW(field.name)] = getattr(instance, field.name + '_id')
        elif isinstance(field, models.FileField):
            res[KW(field.name)] = getattr(instance, field.name).name
        else:
            res[KW(field.name)] = getattr(instance, field.name)
    return res


class UserDefTallyBaseNonStored(Tally, models.Model):

    base = models.TextField(default='null')
    get_tally_body = models.TextField()
    get_value_body = models.TextField(default='"k:instance"')
    handle_change_body = models.TextField()
    filter_value_body = models.TextField(default='true')

    def __init__(self, *args, **kwargs):
        super(Tally, self).__init__(*args, **kwargs)
        self._env = None
        self._decoded_base = None
        self._decoded_get_tally_body = None
        self._decoded_get_value_body = None
        self._decoded_handle_change_body = None
        self._decoded_filter_value_body = None

    @property
    def _base(self):
        if self._decoded_base is None:
            self._decoded_base = json.loads(self.base)
        return self._decoded_base

    @_base.setter
    def _base(self, value):
        self._env = None
        self._decoded_base = value
        self.base = json.dumps(value)

    @property
    def _get_tally_body(self):
        if self._decoded_get_tally_body is None:
            self._decoded_get_tally_body = json.loads(self.get_tally_body)
        return self._decoded_get_tally_body

    @_get_tally_body.setter
    def _get_tally_body(self, value):
        self._decoded_get_tally_body = value
        self.get_tally_body = json.dumps(value)

    @property
    def _get_value_body(self):
        if self._decoded_get_value_body is None:
            self._decoded_get_value_body = json.loads(self.get_value_body)
        return self._decoded_get_value_body

    @_get_value_body.setter
    def _get_value_body(self, value):
        self._decoded_get_value_body = value
        self.get_value_body = json.dumps(value)

    @property
    def _handle_change_body(self):
        if self._decoded_handle_change_body is None:
            self._decoded_handle_change_body = json.loads(
                self.handle_change_body
            )
        return self._decoded_handle_change_body

    @_handle_change_body.setter
    def _handle_change_body(self, value):
        self._decoded_handle_change_body = value
        self.handle_change_body = json.dumps(value)

    @property
    def _filter_value_body(self):
        if self._decoded_filter_value_body is None:
            self._decoded_filter_value_body = json.loads(
                self.filter_value_body
            )
        return self._decoded_filter_value_body

    @_filter_value_body.setter
    def _filter_value_body(self, value):
        self._decoded_filter_value_body = value
        self.filter_value_body = json.dumps(value)

    def refresh_from_db(self, *args, **kwargs):
        self._env = None
        self._decoded_base = None
        self._decoded_get_tally_body = None
        self._decoded_get_value_body = None
        self._decoded_handle_change_body = None
        self._decoded_filter_value_body = None
        return super().refresh_from_db()

    def get_tally(self):
        return self.run(self._get_tally_body)

    def get_value(self, instance):
        return self.run(
            self._get_value_body,
            instance=instance_to_dict(instance),
        )

    def handle_change(self, tally, old_value, new_value):
        return self.run(
            self._handle_change_body,
            tally=tally,
            old_value=old_value,
            new_value=new_value,
        )

    def filter_value(self, value):
        return self.run(self._filter_value_body, value=value)

    def run(self, body, *args, **kwargs):
        if self._env is None:
            self._env = Env()
            run(self._base, self._env)
        return run(body, Env(*args, base_env=self._env, **kwargs))

    class Meta:
        abstract = True


class UserDefTallyBase(DBStored, UserDefTallyBaseNonStored):

    db_name = models.TextField(unique=True)

    def __init__(self, *args, **kwargs):
        super(UserDefTallyBaseNonStored, self).__init__(None)
        super(DBStored, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True
