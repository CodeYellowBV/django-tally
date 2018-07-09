from django import setup
from django.conf import settings

from .testapp import settings as app_settings


# Setup django app
settings.configure(**{
    name: getattr(app_settings, name)
    for name in dir(app_settings)
    if not (name.startswith('__') and name.endswith('__'))
})
setup()


# Sync models
from django.core.management.commands.migrate import (
    Command as MigrationCommand
)  # noqa
from django.db import connections  # noqa
from django.db.migrations.executor import MigrationExecutor  # noqa


cmd = MigrationCommand()
cmd.verbosity = 0
connection = connections['default']
executor = MigrationExecutor(connection)
cmd.sync_apps(connection, executor.loader.unmigrated_apps)
