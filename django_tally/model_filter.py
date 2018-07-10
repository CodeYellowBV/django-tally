from abc import ABC, abstractmethod


class ModelFilterMixin(ABC):
    """
    A mixin to filter signals on Tallies based on the model that sent them.
    """

    @abstractmethod
    def filter_model(self, model):
        """
        Method to filter if a signal should be handled based on the model.

        @param model: Class
            The model that sent the signal.
        @return: bool
            Whether the signal should be handled.
        """

    def handle(self, model, old_data, new_data):
        if self.filter_model(model):
            super().handle(model, old_data, new_data)
