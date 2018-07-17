from django.db import models

from ..db_stored import DBStored
from ...tally import Tally
from ...filter import Filter

from ..lang import run, Env, json, KW


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


class UserDefTallyBaseNonFiltered(Tally, models.Model):

    _base = models.BinaryField(default=b'null')
    _get_tally_body = models.BinaryField()
    _get_value_body = models.BinaryField(default=b'"k:instance"')
    _handle_change_body = models.BinaryField()

    def __init__(self, *args, **kwargs):
        super(Tally, self).__init__(*args, **kwargs)
        self._env = None
        self._decoded_base = None
        self._decoded_get_tally_body = None
        self._decoded_get_value_body = None
        self._decoded_handle_change_body = None

    @property
    def base(self):
        if self._decoded_base is None:
            self._decoded_base = json.loads(self._base.decode())
        return self._decoded_base

    @base.setter
    def base(self, value):
        self.__env = None
        self._decoded_base = value
        self._base = json.dumps(value).encode()

    @property
    def get_tally_body(self):
        if self._decoded_get_tally_body is None:
            self._decoded_get_tally_body = json.loads(
                self._get_tally_body.decode()
            )
        return self._decoded_get_tally_body

    @get_tally_body.setter
    def get_tally_body(self, value):
        self._decoded_get_tally_body = value
        self._get_tally_body = json.dumps(value).encode()

    @property
    def get_value_body(self):
        if self._decoded_get_value_body is None:
            self._decoded_get_value_body = json.loads(
                self._get_value_body.decode()
            )
        return self._decoded_get_value_body

    @get_value_body.setter
    def get_value_body(self, value):
        self._decoded_get_value_body = value
        self._get_value_body = json.dumps(value).encode()

    @property
    def handle_change_body(self):
        if self._decoded_handle_change_body is None:
            self._decoded_handle_change_body = json.loads(
                self._handle_change_body.decode()
            )
        return self._decoded_handle_change_body

    @handle_change_body.setter
    def handle_change_body(self, value):
        self._decoded_handle_change_body = value
        self._handle_change_body = json.dumps(value).encode()

    def refresh_from_db(self, *args, **kwargs):
        self._env = None
        self._decoded_base = None
        self._decoded_get_tally_body = None
        self._decoded_get_value_body = None
        self._decoded_handle_change_body = None
        return super().refresh_from_db()

    def get_tally(self):
        return self.run(self.get_tally_body)

    def get_value(self, instance):
        return self.run(
            self.get_value_body,
            instance=instance_to_dict(instance),
        )

    def handle_change(self, tally, old_value, new_value):
        return self.run(
            self.handle_change_body,
            tally=tally,
            old_value=old_value,
            new_value=new_value,
        )

    def run(self, body, *args, **kwargs):
        if self._env is None:
            self._env = Env()
            run(self.base, self._env)
        return run(body, Env(*args, base_env=self._env, **kwargs))

    class Meta:
        abstract = True


class UserDefTallyBaseNonStored(Filter, UserDefTallyBaseNonFiltered):

    _filter_value_body = models.BinaryField(default=b'true')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._decoded_filter_value_body = None

    @property
    def filter_value_body(self):
        if self._decoded_filter_value_body is None:
            self._decoded_filter_value_body = json.loads(
                self._filter_value_body.decode()
            )
        return self._decoded_filter_value_body

    @filter_value_body.setter
    def filter_value_body(self, value):
        self._decoded_filter_value_body = value
        self._filter_value_body = json.dumps(value).encode()

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        self._decoded_filter_value_body = None

    def filter_value(self, value):
        return self.run(self.filter_value_body, value=value)

    class Meta:
        abstract = True


class UserDefTallyBase(DBStored, UserDefTallyBaseNonStored):

    db_name = models.TextField(unique=True)

    def __init__(self, *args, **kwargs):
        super(UserDefTallyBaseNonFiltered, self).__init__(None)
        super(DBStored, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True
