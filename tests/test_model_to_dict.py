from django.test import TestCase

from django_tally.tally import model_instance_to_dict

from .testapp.models import Foo, Baz


class ModelToDictTest(TestCase):

    def test_foo(self):
        foo = Foo(value=5)
        foo.save()

        self.assertEqual(model_instance_to_dict(foo), {
            'id': foo.id,
            'value': 5,
        })

    def test_baz(self):
        foo = Foo(value=5)
        foo.save()

        baz = Baz(foo=foo)
        baz.save()

        self.assertEqual(model_instance_to_dict(baz), {
            'id': baz.id,
            'foo': foo.id,
            'file': None,
        })
