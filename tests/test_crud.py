from copy import deepcopy
from unittest.mock import Mock, ANY

from django.test import TestCase

from django_tally import Tally, CRUD

from .testapp.models import Foo


class BaseTally(Tally):

    def get_tally(self):
        return None

    def handle_change(self, tally, old_value, new_value):
        return (old_value, new_value)


class CRUDTally(CRUD, BaseTally):
    pass


class CRUDTallyTest(TestCase):

    def test_crud(self):
        crud_tally = CRUDTally()

        crud_tally.handle_create = Mock()
        crud_tally.handle_update = Mock()
        crud_tally.handle_delete = Mock()

        with crud_tally.on(Foo):
            # Initial state
            crud_tally.handle_create.assert_not_called()
            crud_tally.handle_update.assert_not_called()
            crud_tally.handle_delete.assert_not_called()
            # Save model
            foo = Foo()
            foo.save()
            crud_tally.handle_create.assert_called_once_with(ANY, foo)
            crud_tally.handle_update.assert_not_called()
            crud_tally.handle_delete.assert_not_called()
            # Save again
            foo.save()
            crud_tally.handle_create.assert_called_once_with(ANY, foo)
            crud_tally.handle_update.assert_called_once_with(ANY, foo, foo)
            crud_tally.handle_delete.assert_not_called()
            # Delete
            old = deepcopy(foo)
            foo.delete()
            crud_tally.handle_create.assert_called_once_with(ANY, old)
            crud_tally.handle_update.assert_called_once_with(ANY, old, old)
            crud_tally.handle_delete.assert_called_once_with(ANY, old)


class ForwardTest(TestCase):

    def test_calls_forwarded(self):
        crud_tally = CRUDTally()
        with crud_tally.on(Foo):
            # Initial state
            self.assertEqual(crud_tally.tally, None)
            # Save model
            foo = Foo()
            foo.save()
            self.assertEqual(crud_tally.tally, (None, foo))
            # Save model again
            foo.save()
            self.assertEqual(crud_tally.tally, (foo, foo))
            # Delete model
            old = deepcopy(foo)
            foo.delete()
            self.assertEqual(crud_tally.tally, (old, None))
