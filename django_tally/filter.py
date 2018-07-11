class Filter:
    """
    A mixin to filter which values are included on tallies.
    """

    def filter_value(self, value):
        """
        Method to filter if a value should be included.

        @param new_value: Any
            Value of the model.
        @return: bool
            Whether the value should be included.
        """
        raise NotImplementedError

    def handle(self, old_value, new_value):
        if old_value is not None and not self.filter_value(old_value):
            old_value = None
        if new_value is not None and not self.filter_value(new_value):
            new_value = None
        return super().handle(old_value, new_value)
