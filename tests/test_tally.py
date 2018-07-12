from unittest.mock import patch

from django.db.models import Model
from django.test import TestCase

from django_tally import Tally

from .testapp.models import Foo, Bar


class MyTally(Tally):

    def get_tally(self):
        return None


tally = MyTally()


@patch.object(tally, 'handle')
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


class NoEventTally(Tally):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_count = 0
        self.event_count = 0

    def get_tally(self):
        return 'foo'

    def handle_change(self, old_value, new_value):
        self.change_count += 1
        return None

    def handle_event(self, tally, event):
        self.event_count += 1


class NoEventTest(TestCase):

    def test_no_event(self):
        tally = NoEventTally()
        with tally(Foo):
            # Initial value
            self.assertEqual(tally.change_count, 0)
            self.assertEqual(tally.event_count, 0)
            # Save model
            foo = Foo()
            foo.save()
            self.assertEqual(tally.change_count, 1)
            self.assertEqual(tally.event_count, 0)
            # Save model again
            foo.save()
            self.assertEqual(tally.change_count, 2)
            self.assertEqual(tally.event_count, 0)
            # Delete model
            foo.delete()
            self.assertEqual(tally.change_count, 3)
            self.assertEqual(tally.event_count, 0)


class TallyBasicsTest(TestCase):

    def test_reset(self):
        tally = NoEventTally()
        # Initial value
        self.assertEqual(tally.tally, 'foo')
        # Change and reset
        tally.tally = 'bar'
        tally.reset()
        self.assertEqual(tally.tally, 'foo')

    def test_multiple_value_init(self):
        NoEventTally()
        NoEventTally('foo')
        with self.assertRaises(TypeError):
            NoEventTally('foo', 'bar')
