class CRUD:
    """
    Splits handle_change into three seperate methods, handle_create,
    handle_update, and handle_delete.
    """

    def handle_create(self, value):
        """
        Get event based on creation of model instance.

        @param value: Any
            New value of the model.
        @return: Any
            Event triggered by the update.
        """
        return super().handle_change(None, value)

    def handle_update(self, old_value, new_value):
        """
        Get event based on update to model instance.

        @param old_value: Any
            Old value of the model.
        @param new_value: Any
            New value of the model.
        @return: Any
            Event triggered by the update.
        """
        return super().handle_change(old_value, new_value)

    def handle_delete(self, value):
        """
        Get event based on delete to model instance.

        @param data: Any
            Old value of the model.
        @return: Any
            Event triggered by the delete.
        """
        return super().handle_change(value, None)

    def handle_change(self, old_value, new_value):
        if old_value is None:
            return self.handle_create(new_value)
        elif new_value is None:
            return self.handle_delete(old_value)
        else:
            return self.handle_update(old_value, new_value)
