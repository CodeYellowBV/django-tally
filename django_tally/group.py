from abc import ABC, abstractmethod
from collections import defaultdict


class GroupMixin(ABC):
    """
    Mixin that allows for keeping seperate tallies for certain groups based on
    the change that was made.
    When a change causes a model instance to switch group this is considered
    as a delete on the old group and as a create on the new group.
    """

    @abstractmethod
    def group(self, model, data):
        """
        Method to determine to which group a change belongs. If the signal does
        not belong to any group you can return GroupMixin.NoGroup

        @param model: Class
            Model of the changed instance.
        @param data: Mapping
            Data of the model.
        @return: Any
            The group of the change.
        """
        raise NotImplementedError

    def get_tally(self):
        return defaultdict(super().get_tally)

    def handle_change(self, model, old_data, new_data):
        old_group = self.group(model, old_data)
        new_group = self.group(model, new_data)

        # Construct a list of (group, subevent) tuples
        events = []
        if old_group == new_group:
            # Change stays inside the same group
            if new_group is not GroupMixin.NoGroup:
                # Add change event within group
                subevent = super().handle_change(model, old_data, new_data)
                if subevent is not None:
                    events.append((new_group, subevent))
        else:
            # Changee switches group
            if old_data is not None and old_group is not GroupMixin.NoGroup:
                # Add delete event for old group
                subevent = super().handle_change(model, old_data, None)
                if subevent is not None:
                    events.append((old_group, subevent))
            if new_data is not None and new_group is not GroupMixin.NoGroup:
                # Add create event for new group
                subevent = super().handle_change(model, None, new_data)
                if subevent is not None:
                    events.append((new_group, subevent))

        return events

    def handle_event(self, tally, event):
        for group, subevent in event:
            tally[group] = super().handle_event(tally[group], subevent)
        return tally

    class NoGroup:
        pass
