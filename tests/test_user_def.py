from django.test import TestCase
from django.db.utils import ProgrammingError

from django_tally.data.models import Data
from django_tally.user_def.models import UserDefTally
from django_tally.user_def.listen import listen, on
from django_tally.user_def.tally import instance_to_dict
from django_tally.user_def.lang import KW, json

from .testapp.models import Foo, Baz


class TestSimpleCounter(TestCase):

    def setUp(self):
        self.counter = UserDefTally(db_name='counter')
        self.counter.base = json.dumps([
            KW('defn'), KW('transform'), [KW('instance')], [
                KW('if'), [
                    KW('and'),
                    [KW('not-null?'), KW('instance')],
                    [
                        KW('='),
                        [KW('instance'), [KW('quote'), KW('__class__')]],
                        'Foo'
                    ],
                ], [KW('instance'), [KW('quote'), KW('value')]],
                0,
            ],
        ])
        self.counter.get_tally = json.dumps(0)
        self.counter.get_value = json.dumps(KW('instance'))
        self.counter.filter_value = json.dumps([
            KW('>='), [KW('transform'), KW('value')], 3
        ])
        self.counter.handle_change = json.dumps([
            KW('->'), KW('tally'),
            [KW('-'), [KW('transform'), KW('old_value')]],
            [KW('+'), [KW('transform'), KW('new_value')]],
        ])
        self.counter.save()

    def test_counter(self):
        with self.counter.as_tally().on(Foo):
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

    def test_listen(self):
        sub = listen(Foo)

        # Initial value
        self.assertNotStored('counter')
        # Create model
        foo = Foo(value=5)
        foo.save()
        self.assertStored('counter', b'5')
        # Make values count twice
        self.counter.base = json.dumps([
            KW('defn'), KW('transform'), [KW('instance')], [
                KW('if'), [
                    KW('and'),
                    [KW('not-null?'), KW('instance')],
                    [
                        KW('='),
                        [KW('instance'), [KW('quote'), KW('__class__')]],
                        'Foo'
                    ],
                ], [KW('*'), [KW('instance'), [KW('quote'), KW('value')]], 2],
                0,
            ],
        ])
        self.counter.save()
        # Update foo
        foo.value = 6
        foo.save()
        # Note: tally does not know how it used to handle the value so we only
        # get the difference in value *2 added to the tally.
        self.assertStored('counter', b'7')
        # Delete foo
        foo.delete()
        self.assertStored('counter', b'-5')

        sub.close()

    def test_listen_delete(self):
        sub = listen(Foo)

        # Initial value
        self.assertNotStored('counter')
        # Delete counter
        self.counter.delete()
        # Create model
        foo = Foo(value=5)
        foo.save()
        self.assertNotStored('counter')

        sub.close()

    def test_listen_init(self):
        self.counter.delete()

        sub = listen(Foo)

        # Recreate counter
        self.setUp()
        self.assertNotStored('counter')
        foo = Foo(value=5)
        foo.save()
        self.assertStored('counter', b'5')

        sub.close()

    def test_listen_unmigrated_sender(self):

        error_table = 'sender'

        class Sender:

            class objects:
                @classmethod
                def all(cls):
                    print('supppppp')
                    raise ProgrammingError(
                        'relation "{}" does not exist\n'
                        .format(error_table)
                    )

            class _meta:
                db_table = 'sender'

        with on(Foo, tallies=[Sender]):
            pass

        error_table = 'foobar'

        with self.assertRaises(ProgrammingError):
            with on(Foo, tallies=[Sender]):
                pass

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
