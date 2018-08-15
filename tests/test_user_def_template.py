from django.test import TestCase

from django_tally.data.models import Data
from django_tally.user_def.lang import parse
from django_tally.user_def.lang.json import encode
from django_tally.user_def.models import UserDefTemplate

from .testapp.models import Foo


AGGREGATE_PARAMS = {
    'required': ['get_tally', 'add', 'sub'],
    'optional': [
        'base', 'get_value', 'get_nonexisting_value',
        'filter_value', 'transform', 'get_group',
    ],
}
AGGREGATE_TEMPLATE = list(parse("""
(do
  (def agg_base '(do
    (defn agg_sub (tally value)
      (unquote sub))

    (defn agg_add (tally value)
      (unquote add))

    (defn agg_trans (value)
      (unquote (if (def? transform)
        transform
        'value)))))

  (if (def? base)
    (def agg_base (cat
      '(do (unquote base))
      (slice agg_base 1 null))))

  (def res #{
    'base
      agg_base

    'handle_change
      '(-> tally
        (agg_sub (agg_trans old_value))
        (agg_add (agg_trans new_value)))})

  (for key [
      'get_tally
      'get_value
      'get_nonexisting_value
      'filter_value
      'get_group]
    (if (eval '(def? (unquote key)))
      (put res key (eval key))))

  res)
"""))[0]

SUM_PARAMS = {'optional': AGGREGATE_PARAMS['optional']}
SUM_TEMPLATE = list(parse("""(do
  (def res #{
    'get_tally '0
    'add '(+ tally value)
    'sub '(- tally value)})

  (for key [
      'base
      'get_value
      'get_nonexisting_value
      'filter_value
      'get_group]
    (if (eval '(def? (unquote key)))
      (put res key (eval key))))

  res)
"""))[0]


class TestSimpleCounter(TestCase):

    def setUp(self):
        self.aggregate_template = UserDefTemplate(
            params=AGGREGATE_PARAMS,
            template=encode(AGGREGATE_TEMPLATE),
        )
        self.aggregate_template.save()

        self.sum_template = UserDefTemplate(
            params=SUM_PARAMS,
            template=encode(SUM_TEMPLATE),
            parent=self.aggregate_template,
        )
        self.sum_template.save()

    def test_sum_template_transform(self):
        values = self.sum_template.transform({
            'get_value': 1,
            'get_nonexisting_value': 0,
        })
        self.maxDiff = None
        self.assertEqual(values, {
            'base': list(parse("""
                (do
                  (defn agg_sub (tally value)
                    (- tally value))
                  (defn agg_add (tally value)
                    (+ tally value))
                  (defn agg_trans (value)
                    value))
            """))[0],
            'handle_change': list(parse("""
                (-> tally
                  (agg_sub (agg_trans old_value))
                  (agg_add (agg_trans new_value)))
            """))[0],
            'get_value': 1,
            'get_nonexisting_value': 0,
            'get_tally': 0,
        })

    def test_sum_template(self):
        counter = self.sum_template(
            get_value=1,
            get_nonexisting_value=0,
            db_name='counter',
            save=True,
        )

        with counter.as_tally().on(Foo):
            self.assertStored('counter', 0)
            foo1 = Foo()
            foo1.save()
            self.assertStored('counter', 1)
            foo2 = Foo()
            foo2.save()
            self.assertStored('counter', 2)
            foo1.delete()
            self.assertStored('counter', 1)

    def assertStored(self, db_name, value):
        try:
            data = Data.objects.get(name=db_name)
        except Data.DoesNotExist:
            self.fail('No data associated with {}'.format(db_name))
        else:
            self.assertEqual(data.value, value)
