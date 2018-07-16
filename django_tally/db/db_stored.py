import json

from django.db import transaction


class DBStored:
    """
    Mixin to make a Tally save it's data in the database.
    """

    # Name associated with the data
    db_name = None

    def get_db_name(self, value):
        """
        Get the name associated with the tally data associated with this value.
        If this function returns None the value won't be associated with any
        data.

        @param value: Any
            The current value.
        @return: str
            The associated name.
        """
        if value is None:
            return None
        return self.get_db_name_no_none(value)

    def get_db_name_no_none(self, value):
        return self.db_name

    def to_db(self, tally):
        """
        Convert the tally to binary data so that it can be stored in the db.

        @param tally: Any
            The tally to convert.
        @return: bytes
            The converted data.
        """
        return json.dumps(tally).encode()

    def from_db(self, data):
        """
        Convert data from the db to a tally so that it can be used.

        @param data: bytes
            The data from the database as binary data.
        @return: Any
            The converted tally.
        """
        return json.loads(data.decode())

    def __init__(self):
        super().__init__(None)

    def handle_change(self, tally, old_value, new_value):
        old_db_name = self.get_db_name(old_value)
        new_db_name = self.get_db_name(new_value)

        if old_db_name == new_db_name:
            # Change stays inside the same db_name
            if new_db_name is not None:
                # Add change event within db_name
                self._update_data(new_db_name, old_value, new_value)
        else:
            # Change switches db_name
            if old_value is not None and old_db_name is not None:
                # Add delete event for old db_name
                self._update_data(old_db_name, old_value, None)
            if new_value is not None and new_db_name is not None:
                # Add create event for new db_name
                self._update_data(new_db_name, None, new_value)

        return tally

    def _update_data(self, db_name, old_value, new_value):
        from .models import Data
        with transaction.atomic():
            try:
                data = Data.objects.get(name=db_name)
            except Data.DoesNotExist:
                data = Data(name=db_name)
                tally = self.get_tally()
            else:
                tally = self.from_db(data.value)

            tally = super().handle_change(tally, old_value, new_value)

            data.value = self.to_db(tally)
            data.save()
