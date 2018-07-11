from django.test import TestCase

from django_tally import Tally, Sum

from .testapp.models import Foo


class Counter(Sum, Tally):

    def get_value(self, instance):
        return 0 if instance is None else 1


counter = Counter()


class SumTest(TestCase):

    @counter(Foo)
    def test_simple_count(self):
        # Initial value
        self.assertEqual(counter.tally, 0)
        # Create two models but do not save yet
        foo1 = Foo()
        foo2 = Foo()
        self.assertEqual(counter.tally, 0)
        # Save model 1
        foo1.save()
        self.assertEqual(counter.tally, 1)
        # Save model 2
        foo2.save()
        self.assertEqual(counter.tally, 2)
        # Delete model 1
        foo1.delete()
        self.assertEqual(counter.tally, 1)
        # Save model 2 without changes
        foo2.save()
        self.assertEqual(counter.tally, 1)
