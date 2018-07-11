from collections import defaultdict


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
        return defaultdict(super().get_tally)

    def handle_change(self, old_value, new_value):
        old_group = self.get_group(old_value)
        new_group = self.get_group(new_value)

        # Construct a list of (group, subevent) tuples
        events = []
        if old_group == new_group:
            # Change stays inside the same group
            if new_group is not None:
                # Add change event within group
                subevent = super().handle_change(old_value, new_value)
                if subevent is not None:
                    events.append((new_group, subevent))
        else:
            # Change switches group
            if old_value is not None and old_group is not None:
                # Add delete event for old group
                subevent = super().handle_change(old_value, None)
                if subevent is not None:
                    events.append((old_group, subevent))
            if new_value is not None and new_group is not None:
                # Add create event for new group
                subevent = super().handle_change(None, new_value)
                if subevent is not None:
                    events.append((new_group, subevent))

        return events

    def handle_event(self, tally, event):
        for group, subevent in event:
            tally[group] = super().handle_event(tally[group], subevent)
        return tally
