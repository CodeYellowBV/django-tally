from abc import ABC, abstractmethod
from collections import defaultdict


class GroupMixin(ABC):

    def get_tally(self):
        return defaultdict(super().get_tally)

    @abstractmethod
    def group(self, model, old_data, new_data):
        """
        """
        raise NotImplementedError
