from django.db import models
from django.contrib.postgres import fields as pg_fields

from ..data import DBStored
from ..tally import Tally

from .lang import run, Env
from .lang.json import decode
from .instance_wrapper import InstanceWrapper


class UserDefTallyBaseNonStored(models.Model):

    base = pg_fields.JSONField(
        default=None,
        blank=True, null=True,
    )
    get_tally = pg_fields.JSONField(
        default=None,
        blank=True, null=True,
    )
    get_value = pg_fields.JSONField(
        default="k:instance",
        blank=True, null=True,
    )
    get_nonexisting_value = pg_fields.JSONField(
        default=None,
        blank=True, null=True,
    )
    filter_value = pg_fields.JSONField(
        default=True,
        blank=True, null=True,
    )
    handle_change = pg_fields.JSONField(
        default=None,
        blank=True, null=True,
    )

    def as_tally(self, **kwargs):
        base = decode(self.base)
        get_tally = decode(self.get_tally)
        get_value = decode(self.get_value)
        get_nonexisting_value = decode(self.get_nonexisting_value)
        filter_value = decode(self.filter_value)
        handle_change = decode(self.handle_change)

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
                env={'instance': InstanceWrapper(instance)},
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
                    'old_value': old_value,
                    'new_value': new_value,
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
