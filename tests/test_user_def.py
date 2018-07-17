from django.test import TestCase

from django_tally.db.models import UserDefTally, Data
from django_tally.db.lang import KW

from .testapp.models import Foo


class TestSimpleCounter(TestCase):

    def setUp(self):
        self.counter = UserDefTally()
        self.counter.db_name = 'counter'

        self.counter.base = [
            KW('defn'), KW('transform'), [KW('instance')], [
                KW('if'), [
                    KW('and'),
                    [KW('not-null?'), KW('instance')],
                    [
                        KW('='),
                        [KW('instance'), [KW('quote'), KW('__class__')]],
                        'Foo'
                    ],
                ],
                [KW('instance'), [KW('quote'), KW('value')]],
                0,
            ],
        ]
        self.counter.get_tally_body = 0
        self.counter.handle_change_body = [
            KW('->'), KW('tally'),
            [KW('-'), [KW('transform'), KW('old_value')]],
            [KW('+'), [KW('transform'), KW('new_value')]],
        ]
        self.counter.save()

    def test_counter(self):
        with self.counter(Foo):
            # Initial value
            self.assertNotStored('counter')
            # Create model
            foo = Foo(value=1)
            foo.save()
            self.assertStored('counter', b'1')
            # Change value
            foo.value = 3
            foo.save()
            self.assertStored('counter', b'3')
            # Delete model
            foo.delete()
            self.assertStored('counter', b'0')

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
