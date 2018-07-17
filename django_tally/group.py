class Group:
    """
    Mixin that allows for keeping seperate tallies for certain groups based on
    the change that was made.
    When a change causes a model instance to switch group this is considered
    as a delete on the old group and as a create on the new group.
    """

    def get_group(self, value):
        """
        Method to determine to which group a value belongs. A return value of
        None is assumed to mean that the value does not belong to any group.

        @param value: Any
            Value of the model.
        @return: Any
            The group of the value.
        """
        if value is None:
            return None
        return self.get_group_no_none(value)

    def get_group_no_none(self, value):
        """
        Method to determine to which group a value belongs. A return value of
        None is assumed to mean that the value does not belong to any group.
        This differs from the get_group method in that value is guaranteed to
        not be None.

        @param value: Any
            Value of the model, guaranteed to not be None.
        @return: Any
            The group of the value.
        """
        return value

    def get_tally(self):
        return {}

    def handle_change(self, tally, old_value, new_value):
        old_group = self.get_group(old_value)
        new_group = self.get_group(new_value)

        if old_group == new_group:
            # Change stays inside the same group
            if new_group is not None:
                # Add change event within group
                tally[new_group] = super().handle_change(
                    tally[new_group], old_value, new_value
                )
        else:
            # Change switches group
            if old_value is not None and old_group is not None:
                # Add delete event for old group
                tally[old_group] = super().handle_change(
                    tally[old_group], old_value, None
                )
            if new_value is not None and new_group is not None:
                # Add create event for new group
                if new_group not in tally:
                    tally[new_group] = super().get_tally()
                tally[new_group] = super().handle_change(
                    tally[new_group], None, new_value
                )

        return tally
