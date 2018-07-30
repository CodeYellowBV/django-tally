from django.test import TestCase

from django_tally import Tally, Sum
from django_tally.data import DBStored
from django_tally.data.models import Data

from .testapp.models import Foo


class StoredCounter(DBStored, Sum, Tally):

    db_name = 'counter'

    def aggregate_transform(self, value):
        return 0 if value is None else 1


class StoredValueCounter(DBStored, Sum, Tally):

    def filter_value(self, value):
        return isinstance(value, Foo)

    def get_db_name_no_none(self, value):
        return 'counter_{}'.format(value.value)

    def aggregate_transform(self, value):
        return 1


class StoreTest(TestCase):

    def test_simple_store(self):
        counter = StoredCounter()

        with counter.on(Foo):
            # Initial state
            self.assertNotStored('counter')
            self.assertEqual(counter.tally, None)
            # Save model
            foo = Foo()
            foo.save()
            self.assertStored('counter', b'1')
            self.assertEqual(counter.tally, None)
            # Save model again
            foo.save()
            self.assertStored('counter', b'1')
            self.assertEqual(counter.tally, None)
            # Delete model
            foo.delete()
            self.assertStored('counter', b'0')
            self.assertEqual(counter.tally, None)

    def test_multi_name_store(self):
        counter = StoredValueCounter()

        with counter.on(Foo):
            # Initial state
            self.assertNotStored('counter_0')
            self.assertNotStored('counter_1')
            self.assertEqual(counter.tally, None)
            # Save model
            foo = Foo(value=0)
            foo.save()
            self.assertStored('counter_0', b'1')
            self.assertNotStored('counter_1')
            self.assertEqual(counter.tally, None)
            # Change value and save
            foo.value = 1
            foo.save()
            self.assertStored('counter_0', b'0')
            self.assertStored('counter_1', b'1')
            self.assertEqual(counter.tally, None)
            # Delete model
            foo.delete()
            self.assertStored('counter_0', b'0')
            self.assertStored('counter_1', b'0')
            self.assertEqual(counter.tally, None)

    def assertStored(self, db_name, value):
        try:
            data = Data.objects.get(name=db_name)
        except Data.DoesNotExist:
            self.fail('No data associated with {}'.format(db_name))
        else:
            self.assertEqual(data.value, value)

    def assertNotStored(self, db_name):
        with self.assertRaises(Data.DoesNotExist):
            Data.objects.get(name=db_name)
