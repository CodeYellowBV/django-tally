from django.test import TestCase
from django.db.utils import ProgrammingError

from django_tally.data.models import Data
from django_tally.user_def.models import UserDefTally
from django_tally.user_def.listen import listen, on
from django_tally.user_def.lang import KW
from django_tally.user_def.lang.json import encode

from .testapp.models import Foo


class TestSimpleCounter(TestCase):

    def setUp(self):
        self.counter = UserDefTally(db_name='counter')
        self.counter.base = encode([
            KW('defn'), KW('transform'), [KW('instance')], [
                KW('if'), [
                    KW('and'),
                    [KW('not_null?'), KW('instance')],
                    [
                        KW('='),
                        [KW('instance'), [KW('quote'), KW('__class__')]],
                        'Foo'
                    ],
                ], [KW('instance'), [KW('quote'), KW('value')]],
                0,
            ],
        ])
        self.counter.get_tally = encode(0)
        self.counter.get_value = encode(KW('instance'))
        self.counter.filter_value = encode([
            KW('>='), [KW('transform'), KW('value')], 3
        ])
        self.counter.handle_change = encode([
            KW('->'), KW('tally'),
            [KW('-'), [KW('transform'), KW('old_value')]],
            [KW('+'), [KW('transform'), KW('new_value')]],
        ])
        self.counter.save()

    def test_counter(self):
        with self.counter.as_tally().on(Foo):
            # Initial value
            self.assertStored('counter', 0)
            # Create model
            foo = Foo(value=5)
            foo.save()
            self.assertStored('counter', 5)
            # Change value below threshold
            foo.value = 2
            foo.save()
            self.assertStored('counter', 0)
            # Change value again
            foo.value = 3
            foo.save()
            self.assertStored('counter', 3)
            # Delete model
            foo.delete()
            self.assertStored('counter', 0)

    def test_counter_refreshed(self):
        self.counter.refresh_from_db()
        self.test_counter()

    def test_listen(self):
        sub = listen(Foo)

        # Initial value
        self.assertStored('counter', 0)
        # Create model
        foo = Foo(value=5)
        foo.save()
        self.assertStored('counter', 5)
        # Make values count twice
        self.counter.base = encode([
            KW('defn'), KW('transform'), [KW('instance')], [
                KW('if'), [
                    KW('and'),
                    [KW('not_null?'), KW('instance')],
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
        self.assertStored('counter', 7)
        # Delete foo
        foo.delete()
        self.assertStored('counter', -5)

        sub.close()

    def test_listen_delete(self):
        sub = listen(Foo)

        # Initial value
        self.assertStored('counter', 0)
        # Delete counter
        self.counter.delete()
        # Create model
        foo = Foo(value=5)
        foo.save()
        self.assertStored('counter', 0)

        sub.close()

    def test_listen_init(self):
        self.counter.delete()

        sub = listen(Foo)

        # Recreate counter
        self.setUp()
        self.assertStored('counter', 0)
        foo = Foo(value=5)
        foo.save()
        self.assertStored('counter', 5)

        sub.close()

    def test_listen_unmigrated_sender(self):

        error_table = 'sender'

        class Sender:

            class objects:
                @classmethod
                def all(cls):
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
