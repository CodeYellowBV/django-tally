import json

from django.db import transaction


class DBStored:
    """
    Mixin to make a Tally save it's data in the database.
    """

    # Name associated with the data
    db_name = None

    def __init__(self):
        super().__init__(None)
        self.ensure_data()

    def ensure_data(self):
        from .models import Data

        if not Data.objects.filter(name=self.db_name).exists():
            Data(
                name=self.db_name,
                value=json.dumps(self.get_tally()),
            ).save()

    def handle_change(self, tally, old_value, new_value):
        from .models import Data

        with transaction.atomic():
            data = Data.objects.get(name=self.db_name)

            tally = json.loads(data.value)
            tally = super().handle_change(tally, old_value, new_value)

            data.value = json.dumps(tally)
            data.save()
