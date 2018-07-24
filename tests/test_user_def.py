from django.test import TestCase

from django_tally.data.models import Data
from django_tally.user_def.models import UserDefTally
from django_tally.user_def.user_def_tally_base import instance_to_dict
from django_tally.user_def.lang import KW

from .testapp.models import Foo, Baz


class TestSimpleCounter(TestCase):

    def setUp(self):
        self.counter = UserDefTally(db_name='counter')

        self.counter._base = [
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
        self.counter._get_tally_body = 0
        self.counter._get_value_body = KW('instance')
        self.counter._filter_value_body = [
            KW('>='), [KW('transform'), KW('value')], 3
        ]
        self.counter._handle_change_body = [
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
            foo = Foo(value=5)
            foo.save()
            self.assertStored('counter', b'5')
            # Change value below threshold
            foo.value = 2
            foo.save()
            self.assertStored('counter', b'0')
            # Change value again
            foo.value = 3
            foo.save()
            self.assertStored('counter', b'3')
            # Delete model
            foo.delete()
            self.assertStored('counter', b'0')

    def test_counter_refreshed(self):
        self.counter.refresh_from_db()
        self.test_counter()

    def test_instance_to_dict(self):
        foo = Foo()
        foo.save()
        baz = Baz(foo=foo)
        baz.save()
        self.assertEqual(instance_to_dict(baz), {
            KW('__class__'): 'Baz',
            KW('id'): baz.id,
            KW('foo'): foo.id,
            KW('file'): None,
        })

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
