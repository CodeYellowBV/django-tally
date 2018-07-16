from unittest.mock import patch, Mock

from django.db.models import Model
from django.test import TestCase

from django_tally import Tally

from .testapp.models import Foo, Bar


class MyTally(Tally):

    def get_tally(self):
        return None


tally = MyTally()


@patch.object(tally, '_handle')
class TallyHandleTest(TestCase):

    @tally(Foo)
    def test_subscription(self, handle):
        # Initial state
        handle.assert_not_called()
        # Save model
        foo = Foo()
        foo.save()
        handle.assert_called_once_with(None, foo)

    def test_no_subscription(self, handle):
        # Initial state
        handle.assert_not_called()
        # Save model
        foo = Foo()
        foo.save()
        handle.assert_not_called()

    def test_closed_subscription(self, handle):
        # Initial state
        handle.assert_not_called()
        # Open subscription and save model
        foo = Foo()
        with tally(Foo):
            foo.save()
            handle.assert_called_once_with(None, foo)
        handle.reset_mock()
        # Save model again
        foo.save()
        handle.assert_not_called()

    def test_multisub(self, handle):
        sub = tally.listen(Foo, Bar)
        # Initial state
        handle.assert_not_called()
        # Save Foo model
        foo = Foo()
        foo.save()
        handle.assert_called_once_with(None, foo)
        handle.reset_mock()
        # Save Bar model
        bar = Bar()
        bar.save()
        handle.assert_called_once_with(None, bar)

        sub.close()

    def test_basesub(self, handle):
        sub = tally.listen(Model)
        # Initial state
        handle.assert_not_called()
        # Save Foo model
        foo = Foo()
        foo.save()
        handle.assert_called_once_with(None, foo)
        handle.reset_mock()
        # Save Bar model
        bar = Bar()
        bar.save()
        handle.assert_called_once_with(None, bar)

        sub.close()


class FooTally(Tally):

    def get_tally(self):
        return 'foo'

    def handle_change(self, tally, old_value, new_value):
        return tally


class TallyBasicsTest(TestCase):

    def test_reset(self):
        tally = FooTally()
        # Initial value
        self.assertEqual(tally.tally, 'foo')
        # Change and reset
        tally.tally = 'bar'
        tally.reset()
        self.assertEqual(tally.tally, 'foo')

    def test_multiple_value_init(self):
        FooTally()
        FooTally('foo')
        with self.assertRaises(TypeError):
            FooTally('foo', 'bar')

    def test_handle_change_calls(self):
        tally = FooTally()
        tally.handle_change = Mock()

        # Initial value
        self.assertEqual(tally.handle_change.call_count, 0)
        # Two values
        tally._handle('foo', 'bar')
        self.assertEqual(tally.handle_change.call_count, 1)
        # Only new value
        tally._handle('foo', None)
        self.assertEqual(tally.handle_change.call_count, 2)
        # Only old value
        tally._handle(None, 'bar')
        self.assertEqual(tally.handle_change.call_count, 3)
        # Only old value
        tally._handle(None, None)
        self.assertEqual(tally.handle_change.call_count, 3)
