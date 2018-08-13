from django.test import TestCase

from django_tally import Group
from django_tally.data.models import Data
from django_tally.user_def.models import UserDefGroupTally
from django_tally.user_def.lang import KW, json

from .testapp.models import Foo


class TestValueCounter(TestCase):

    def setUp(self):
        self.counter = UserDefGroupTally(db_name='counter')
        self.counter.base = json.dumps([
            KW('defn'), KW('transform'), [KW('value')], [
                KW('if'), [
                    KW('and'),
                    [KW('not-null?'), KW('value')],
                    [
                        KW('='),
                        [KW('value'), [KW('quote'), KW('__class__')]],
                        'Foo',
                    ],
                ],
                1,
                0,
            ]
        ])
        self.counter.get_tally = json.dumps(0)
        self.counter.get_group = json.dumps([
            KW('if'), [
                KW('and'),
                [KW('not-null?'), KW('value')],
                [
                    KW('='),
                    [KW('value'), [KW('quote'), KW('__class__')]],
                    'Foo',
                ],
            ],
            [KW('str'), [KW('value'), [KW('quote'), KW('value')]]],
            None,
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
            self.assertStoredGroups({})
            # Save model with value 1
            foo1 = Foo(value=1)
            foo1.save()
            self.assertStoredGroups({'1': 1})
            # Save model with value 1
            foo2 = Foo(value=1)
            foo2.save()
            self.assertStoredGroups({'1': 2})
            # Save model with value 2
            foo3 = Foo(value=2)
            foo3.save()
            self.assertStoredGroups({'1': 2, '2': 1})
            # Switch value of model
            foo1.value = 2
            foo1.save()
            self.assertStoredGroups({'1': 1, '2': 2})
            # Delete model
            foo3.delete()
            self.assertStoredGroups({'1': 1, '2': 1})

    def test_counter_refreshed(self):
        self.counter.refresh_from_db()
        self.test_counter()

    def assertStoredGroups(self, values):
        try:
            data = Data.objects.get(name=self.counter.db_name)
        except Data.DoesNotExist:
            self.fail(
                'No data associated with {}'
                .format(self.counter.db_name)
            )

        groups = json.loads(data.value)
        for key in values:
            if key not in groups:
                groups[key] = super(Group, self.counter.as_tally()).get_tally()
        errors = [
            (key, groups[key], value)
            for key, value in values.items()
            if groups[key] != value
        ]
        if errors:
            self.fail('{{\n{}\n}}'.format('\n'.join(
                '    {!r}: {!r} != {!r},'.format(*error)
                for error in errors
            )))
