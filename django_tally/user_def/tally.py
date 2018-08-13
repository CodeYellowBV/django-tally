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


class UserDefTallyBaseNonStored(models.Model):

    base = models.TextField(default='null')
    get_tally = models.TextField()
    get_value = models.TextField(default='"k:instance"')
    get_nonexisting_value = models.TextField(default='null')
    filter_value = models.TextField(default='true')
    handle_change = models.TextField()

    def as_tally(self, **kwargs):
        base = json.loads(self.base)
        get_tally = json.loads(self.get_tally)
        get_value = json.loads(self.get_value)
        get_nonexisting_value = json.loads(self.get_nonexisting_value)
        filter_value = json.loads(self.filter_value)
        handle_change = json.loads(self.handle_change)

        env = Env()
        run(base, env)

        return self.UserTally(
            env=env,
            get_tally=get_tally,
            get_value=get_value,
            get_nonexisting_value=get_nonexisting_value,
            filter_value=filter_value,
            handle_change=handle_change,
            **kwargs
        )

    class UserTally(Tally):

        def __init__(
            self, env, get_tally, get_value, get_nonexisting_value,
            filter_value, handle_change,
        ):
            super().__init__(None)
            self._env = env
            self._get_tally = get_tally
            self._get_value = get_value
            self._get_nonexisting_value = get_nonexisting_value
            self._filter_value = filter_value
            self._handle_change = handle_change

        def get_tally(self):
            return run(self._get_tally, Env(base_env=self._env))

        def get_value(self, instance):
            return run(self._get_value, Env(
                env={'instance': instance_to_dict(instance)},
                base_env=self._env,
            ))

        def get_nonexisting_value(self):
            return run(self._get_nonexisting_value, Env(base_env=self._env))

        def filter_value(self, value):
            return run(self._filter_value, Env(
                env={'value': value},
                base_env=self._env,
            ))

        def handle_change(self, tally, old_value, new_value):
            return run(self._handle_change, Env(
                env={
                    'tally': tally,
                    'old-value': old_value,
                    'new-value': new_value,
                },
                base_env=self._env,
            ))

    class Meta:
        abstract = True


class UserDefTallyBase(UserDefTallyBaseNonStored):

    db_name = models.TextField(unique=True)

    def as_tally(self):
        return super().as_tally(db_name=self.db_name)

    class UserTally(DBStored, UserDefTallyBaseNonStored.UserTally):

        def __init__(self, db_name, **kwargs):
            super(DBStored, self).__init__(**kwargs)
            self.db_name = db_name
            self.ensure_data()

    class Meta:
        abstract = True
