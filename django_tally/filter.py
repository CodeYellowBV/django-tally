from abc import ABC, abstractmethod


class FilterMixin(ABC):
    """
    A mixin to filter signals on Tallies.
    """

    @abstractmethod
    def filter(self, model, old_data, new_data):
        """
        Method to filter if a change should be handled based on the model.

        @param model: Class
            Model of the changed instance.
        @param old_data: Mapping
            Old data of the model.
        @param new_data: Mapping
            New data of the model.
        @return: bool
            Whether the change should be handled.
        """
        raise NotImplementedError

    def handle_change(self, model, old_data, new_data):
        if not self.filter(model, old_data, new_data):
            return None
        return super().handle_change(model, old_data, new_data)
