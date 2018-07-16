import operator


class Aggregate:
    """
    Mixin that given an identity, operator, inverse_operator, and a method
    implementation to gather a value based on a model instance value that keeps
    a tally for this aggregate.
    """

    # The identity of the aggregation operation
    aggregate_id = None

    def aggregate_add(self, aggregate, value):
        """
        Add a value to the aggregate.

        @param aggregate: Any
            The current aggregate.
        @param value: Any
            The value to add.
        @return: Any
            The aggregate after the value was added.
        """
        raise NotImplementedError

    def aggregate_sub(self, aggregate, value):
        """
        Subtract a value from the aggregate.

        @param aggregate: Any
            The current aggregate.
        @param value: Any
            The value to subtract.
        @return: Any
            The aggregate after the value was removed.
        """
        raise NotImplementedError

    def aggregate_transform(self, value):
        """
        Transforms the value before it is added to or removed from the
        aggregate.

        @param value: Any
           The value to transform.
        @return: Any
            The transformed value.
        """
        return value

    def get_tally(self):
        return self.aggregate_id

    def handle_change(self, tally, old_value, new_value):
        if old_value is None:
            old_value = self.aggregate_id
        else:
            old_value = self.aggregate_transform(old_value)

        if new_value is None:
            new_value = self.aggregate_id
        else:
            new_value = self.aggregate_transform(new_value)

        tally = self.aggregate_sub(tally, old_value)
        tally = self.aggregate_add(tally, new_value)

        return tally


class Sum(Aggregate):
    """
    Subclass of AggregateMixin that provides the right operations and identity
    for a sum aggregate.
    """
    aggregate_id = 0
    aggregate_add = operator.add
    aggregate_sub = operator.sub


class Product(Aggregate):
    """
    Subclass of AggregateMixin that provides the right operations and identity
    for a product aggregate.
    """
    aggregate_id = 1
    aggregate_add = operator.mul
    aggregate_sub = operator.truediv
