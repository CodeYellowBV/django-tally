from abc import ABC, abstractmethod
import operator


class AggregateMixin(ABC):
    """
    Mixin that given an identity, operator, inverse_operator, and a method
    implementation to gather a value based on a model instance keeps a tally
    for this aggregate.
    """

    aggregate_operator = None
    aggregate_operator_inverse = None
    aggregate_identity = None

    @abstractmethod
    def get_value(self, model, data):
        """
        Get value for the aggregate based on a model instance.

        @param model: Class
            Model of the updated instance.
        @param data: Mapping
            Data of the model.
        """

    def get_tally(self):
        return self.aggregate_identity

    def handle_create(self, model, data):
        return (
            self.aggregate_identity,
            self.get_value(model, data),
        )

    def handle_update(self, model, old_data, new_data):
        return (
            self.get_value(model, old_data),
            self.get_value(model, new_data),
        )

    def handle_delete(self, model, data):
        return (
            self.get_value(model, data),
            self.aggregate_identity,
        )

    def handle_event(self, tally, event):
        old_value, new_value = event
        tally1 = self.aggregate_operator_inverse(tally, old_value)
        tally2 = self.aggregate_operator(tally1, new_value)
        return tally2


class SumMixin(AggregateMixin):
    """
    Subclass of AggregateMixin that provides the right operator, inverse
    operator, and identity for a sum aggregate.
    """

    aggregate_operator = operator.add
    aggregate_operator_inverse = operator.sub
    aggregate_identity = 0


class ProductMixin(AggregateMixin):
    """
    Subclass of AggregateMixin that provides the right operator, inverse
    operator, and identity for a product aggregate.
    """

    aggregate_operator = operator.mul
    aggregate_operator_inverse = operator.truediv
    aggregate_identity = 1
