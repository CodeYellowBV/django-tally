from django.test import TestCase
from django_tally.user_def.instance_wrapper import InstanceWrapper
from django_tally.user_def.lang import KW

from .testapp.models import Foo, Baz


class InstanceWrapperTest(TestCase):

    def test_instance_wapper(self):
        foo = Foo(value=5)
        foo.save()
        baz = Baz(foo=foo)
        baz.save()

        wrapped_baz = InstanceWrapper(baz)
        self.assertEqual(wrapped_baz[KW('__class__')], 'Baz')
        self.assertEqual(wrapped_baz[KW('id')], baz.id)
        self.assertEqual(wrapped_baz[KW('file')], None)
        with self.assertRaises(KeyError):
            wrapped_baz[KW('foobar')]

        wrapped_foo = wrapped_baz[KW('foo')]
        self.assertEqual(wrapped_foo[KW('__class__')], 'Foo')
        self.assertEqual(wrapped_foo[KW('value')], 5)

        wrapped_bazs = wrapped_foo[KW('bazs')]
        self.assertEqual(len(wrapped_bazs), 1)
        self.assertEqual(
            wrapped_bazs[0][KW('__class__')],
            wrapped_baz[KW('__class__')],
        )
        self.assertEqual(
            wrapped_bazs[0][KW('id')],
            wrapped_baz[KW('id')],
        )
