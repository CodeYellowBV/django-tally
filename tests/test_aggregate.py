from django.test import TestCase

from buckets import Bucket, SumMixin

from .testapp.models import Foo


class ModelCounter(SumMixin, Bucket):
    def get_value(self, model, data):
        return 1


class ModelCounterTest(TestCase):

    def setUp(self):
        self.counter = ModelCounter()
        self.counter.listen(Foo)

    def test_simple_count(self):
        self.assertCount(0)

        # Create two models but do not save yet
        foo1 = Foo()
        foo2 = Foo()

        self.assertCount(0)

        # Save model 1
        foo1.save()

        self.assertCount(1)

        # Save model 2
        foo2.save()

        self.assertCount(2)

        # Delete model 1
        foo1.delete()

        self.assertCount(1)

        # Save model 2 without changes
        foo2.save()

        self.assertCount(1)

    def assertCount(self, value):
        self.assertEqual(self.counter.tally, value)
