from django.test import TestCase

from django_tally import Tally, Sum, Group

from .testapp.models import Foo


class OddEvenCounter(Group, Sum, Tally):

    def aggregate_transform(self, value):
        return 0 if value is None else 1

    def get_group_no_none(self, value):
        return 'even' if value.value % 2 == 0 else 'odd'


class NumberCounter(Group, Sum, Tally):

    def get_value(self, value):
        if not isinstance(value, Foo):
            return None
        return value.value

    def aggregate_transform(self, value):
        return 1


class GroupTest(TestCase):

    def test_odd_even(self):
        counter = OddEvenCounter()

        with counter(Foo):
            # Initial value
            self.assertEqualGroups(counter.tally, {'even': 0, 'odd': 0})
            # Save model with even value
            even1 = Foo(value=0)
            even1.save()
            self.assertEqualGroups(counter.tally, {'even': 1, 'odd': 0})
            # Save model with odd value
            odd1 = Foo(value=1)
            odd1.save()
            self.assertEqualGroups(counter.tally, {'even': 1, 'odd': 1})
            # Save model with even but different value
            even2 = Foo(value=2)
            even2.save()
            self.assertEqualGroups(counter.tally, {'even': 2, 'odd': 1})
            # Change model from even to odd
            even1.value = 1
            even1.save()
            self.assertEqualGroups(counter.tally, {'even': 1, 'odd': 2})
            # Change value but remain even
            even2.value = 4
            even2.save()
            self.assertEqualGroups(counter.tally, {'even': 1, 'odd': 2})

    def test_number_counter(self):
        counter = NumberCounter()

        with counter(Foo):
            Foo(value=1).save()
            self.assertEqualGroups(counter.tally, {1: 1})
            Foo(value=2).save()
            self.assertEqualGroups(counter.tally, {1: 1, 2: 1})
            Foo(value=3).save()
            self.assertEqualGroups(counter.tally, {1: 1, 2: 1, 3: 1})
            Foo(value=2).save()
            self.assertEqualGroups(counter.tally, {1: 1, 2: 2, 3: 1})

    def assertEqualGroups(self, groups, values):
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
