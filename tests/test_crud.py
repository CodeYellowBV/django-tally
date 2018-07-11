from copy import deepcopy
from unittest.mock import patch, ANY

from django.test import TestCase

from django_tally import Tally, CRUD

from .testapp.models import Foo


class BaseTally(Tally):

    def get_tally(self):
        return None

    def handle_change(self, old_value, new_value):
        return (old_value, new_value)

    def handle_event(self, tally, event):
        return None


class CRUDTally(CRUD, BaseTally):
    pass


crud_tally = CRUDTally()


@patch.object(crud_tally, 'handle_create')
@patch.object(crud_tally, 'handle_update')
@patch.object(crud_tally, 'handle_delete')
class CRUDTallyTest(TestCase):

    @crud_tally(Foo)
    def test_crud(self, delete, update, create):
        # Initial state
        create.assert_not_called()
        update.assert_not_called()
        delete.assert_not_called()
        # Save model
        foo = Foo()
        foo.save()
        create.assert_called_once_with(foo)
        update.assert_not_called()
        delete.assert_not_called()
        # Save again
        foo.save()
        create.assert_called_once_with(foo)
        update.assert_called_once_with(foo, foo)
        delete.assert_not_called()
        # Delete
        old = deepcopy(foo)
        foo.delete()
        create.assert_called_once_with(old)
        update.assert_called_once_with(old, old)
        delete.assert_called_once_with(old)


@patch.object(crud_tally, 'handle_event')
class ForwardTest(TestCase):

    @crud_tally(Foo)
    def test_calls_forwarded(self, handle_event):
        # Initial state
        handle_event.assert_not_called()
        # Save model
        foo = Foo()
        foo.save()
        handle_event.assert_called_once_with(ANY, (None, foo))
        handle_event.reset_mock()
        # Save model again
        foo.save()
        handle_event.assert_called_once_with(ANY, (foo, foo))
        handle_event.reset_mock()
        # Delete model
        old = deepcopy(foo)
        foo.delete()
        handle_event.assert_called_once_with(ANY, (old, None))
