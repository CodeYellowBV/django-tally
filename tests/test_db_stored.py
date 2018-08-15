from django.test import TestCase

from django_tally import Tally, Sum
from django_tally.data import DBStored
from django_tally.data.models import Data

from .testapp.models import Foo


class StoredCounter(DBStored, Sum, Tally):

    db_name = 'counter'

    def aggregate_transform(self, value):
        return 0 if value is None else 1


class StoreTest(TestCase):

    def test_simple_store(self):
        counter = StoredCounter()

        with counter.on(Foo):
            # Initial state
            self.assertStored('counter', 0)
            self.assertEqual(counter.tally, None)
            # Save model
            foo = Foo()
            foo.save()
            self.assertStored('counter', 1)
            self.assertEqual(counter.tally, None)
            # Save model again
            foo.save()
            self.assertStored('counter', 1)
            self.assertEqual(counter.tally, None)
            # Delete model
            foo.delete()
            self.assertStored('counter', 0)
            self.assertEqual(counter.tally, None)

    def assertStored(self, db_name, value):
        try:
            data = Data.objects.get(name=db_name)
        except Data.DoesNotExist:
            self.fail('No data associated with {}'.format(db_name))
        else:
            self.assertEqual(data.value, value)
