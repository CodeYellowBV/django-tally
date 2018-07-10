from django.test import TestCase

from django_tally import Tally, SumMixin, GroupMixin

from .testapp.models import Foo


class OddEvenCounter(GroupMixin, SumMixin, Tally):
    """
    Tallies the amount of odd or even values.
    """

    def get_value(self, model, data):
        return 1

    def group(self, model, data):
        if data is None:
            return GroupMixin.NoGroup
        return 'even' if data['value'] % 2 == 0 else 'odd'


class GroupTest(TestCase):

    def test_grouping(self):
        counter = OddEvenCounter()
        with counter.subscribe(Foo):
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

    def assertEqualGroups(self, groups, values):
        for key, value in values.items():
            self.assertEqual(groups[key], value)
