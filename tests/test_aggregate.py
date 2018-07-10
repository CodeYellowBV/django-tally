from django.test import TestCase
from django.db.models import Model

from django_tally import Tally, SumMixin, ProductMixin

from .testapp.models import Foo


class ModelCounter(SumMixin, Tally):
    """
    Tallies the amount of models.
    """

    def get_value(self, model, data):
        return 1


class FooProduct(ProductMixin, Tally):
    """
    Tallies the product of the value attribute of Foo instances.
    """

    def accept_model(self, model):
        return issubclass(model, Foo)

    def get_value(self, model, data):
        return data['value']


class ModelCounterTest(TestCase):

    def test_simple_count(self):
        counter = ModelCounter()
        sub = counter.listen(Foo)

        # Initial value
        self.assertEqual(counter.tally, 0)

        # Create two models but do not save yet
        foo1 = Foo()
        foo2 = Foo()
        self.assertEqual(counter.tally, 0)

        # Save model 1
        foo1.save()
        self.assertEqual(counter.tally, 1)

        # Save model 2
        foo2.save()
        self.assertEqual(counter.tally, 2)

        # Delete model 1
        foo1.delete()
        self.assertEqual(counter.tally, 1)

        # Save model 2 without changes
        foo2.save()
        self.assertEqual(counter.tally, 1)

        sub.close()

    def test_product(self):
        product = FooProduct()
        with product.subscribe(Model):
            # Initial value
            self.assertEqual(product.tally, 1)

            # Create two models but do not save yet
            foo1 = Foo(value=3)
            foo2 = Foo(value=5)
            self.assertEqual(product.tally, 1)

            # Save model 1
            foo1.save()
            self.assertEqual(product.tally, 3)

            # Save model 2
            foo2.save()
            self.assertEqual(product.tally, 15)

            # Delete model 1
            foo1.delete()
            self.assertEqual(product.tally, 5)

            # Save model 2 without changes
            foo2.save()
            self.assertEqual(product.tally, 5)

            # Save model 2 with changes
            foo2.value = 7
            foo2.save()
            self.assertEqual(product.tally, 7)

    def test_disconnect(self):
        counter = ModelCounter()
        with counter.subscribe(Foo):
            # Initial value
            self.assertEqual(counter.tally, 0)

            # Save a model
            Foo().save()
            self.assertEqual(counter.tally, 1)

        # Save a model when counter is closed
        Foo().save()
        self.assertEqual(counter.tally, 1)
