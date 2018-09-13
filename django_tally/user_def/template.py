from importlib import import_module

from django.db import models
from django.contrib.postgres import fields as pg_fields

from .lang import run, Env, KW
from .lang.json import encode, decode


class UserDefTemplateBase(models.Model):

    TALLY = 'django_tally.user_def.models.UserDefTally'
    GROUP_TALLY = 'django_tally.user_def.models.UserDefGroupTally'

    params = pg_fields.JSONField(default=dict, blank=True)
    template = pg_fields.JSONField(
        default=None,
        blank=True, null=True,
    )
    parent = models.ForeignKey(
        'self', models.CASCADE,
        blank=True, null=True,
        related_name='children',
    )

    def __call__(self, *args, save=False, **kwargs):
        db_name = kwargs.pop('db_name')
        args = self.transform(dict(*args, **kwargs))
        args = {
            key: encode(value)
            for key, value in args.items()
        }

        tally_spec = self.GROUP_TALLY if 'get_group' in args else self.TALLY
        module, _, name = tally_spec.rpartition('.')
        tally_class = getattr(import_module(module), name)
        tally = tally_class(db_name=db_name, **args)

        if save:
            tally.save()

        return tally

    def transform(self, args):
        # Assert given args are correct
        req = set(self.params.get('required', []))
        opt = set(self.params.get('optional', []))
        given = set(args)

        missing = req - given
        extra = given - req - opt

        assert not missing and not extra, (
            'Incorrect call.' +
            (' Missing: {}' + ', '.join(missing) + '.' if missing else '') +
            (' Extra: {}' + ', '.join(extra) + '.' if extra else '')
        )

        # Run template to get new args
        args = {
            key.value if isinstance(key, KW) else key: value
            for key, value in run(decode(self.template), Env(env=args)).items()
        }

        # Run args through parent if there is one
        if self.parent:
            args = self.parent.transform(args)

        return args

    class Meta:
        abstract = True
