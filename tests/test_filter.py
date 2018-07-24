from django.test import TestCase

from django_tally import Tally, Filter, Sum

from .testapp.models import Foo, Bar


class FooCounter(Filter, Sum, Tally):

    def filter_value(self, value):
        return isinstance(value, Foo)

    def aggregate_transform(self, value):
        return 1


class FilterTest(TestCase):

    def test_filter(self):
        foo_counter = FooCounter()

        with foo_counter.on(Foo, Bar):
            # Initial value
            self.assertEqual(foo_counter.tally, 0)
            # Save Foo instance
            foo = Foo()
            foo.save()
            self.assertEqual(foo_counter.tally, 1)
            # Delete Foo instance
            foo.delete()
            self.assertEqual(foo_counter.tally, 0)
            # Save Bar instance
            bar = Bar()
            bar.save()
            self.assertEqual(foo_counter.tally, 0)
            # Delete Bar instance
            bar.delete()
            self.assertEqual(foo_counter.tally, 0)
