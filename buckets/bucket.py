from abc import ABC, abstractmethod

from django.db import models
from django.db.models.signals import post_init, post_save, post_delete
from django.dispatch import receiver


def model_instance_to_dict(instance):
    """
    Converts a Django model instance to a dict of values for all it's concrete
    non many to many fields.

    @param instance: Model The model instance to convert.
    @return: dict          The generated dict of values.
    """
    res = {}

    for field in instance._meta.get_fields():
        if not field.concrete or field.many_to_many:
            continue

        if isinstance(field, models.ForeignKey):
            value = getattr(instance, field.name + '_id')
        elif isinstance(field, models.FileField):
            value = str(getattr(instance, field.name))
        else:
            value = getattr(instance, field.name)

        res[field.name] = value

    return res


class Bucket(ABC):
    """
    Abstract base class for a Bucket.
    A bucket is a container that keeps track of a tally and updates this tally
    based on changes happening to model instances.
    """

    @abstractmethod
    def get_tally(self):
        """
        Get initial value for the tally.

        @return: Any Initial value for the tally.
        """

    @abstractmethod
    def handle_create(self, model, data):
        """
        Get event based on creation of model instance.

        @param model: Class  Model of the updated instance.
        @param data: Mapping New data of the model.
        @return: Any         Event triggered by the update.
        """

    @abstractmethod
    def handle_update(self, model, old_data, new_data):
        """
        Get event based on update to model instance.

        @param model: Class      Model of the updated instance.
        @param old_data: Mapping Old data of the model.
        @param new_data: Mapping New data of the model.
        @return: Any             Event triggered by the update.
        """

    @abstractmethod
    def handle_delete(self, model, data):
        """
        Get event based on delete to model instance.

        @param model: Class  Model of the updated instance.
        @param data: Mapping Old data of the model.
        @return: Any         Event triggered by the delete.
        """

    @abstractmethod
    def handle_event(self, tally, event):
        """
        Update tally based on event.

        @param tally: Any The current tally.
        @param event: Any Event triggered.
        @return: Any      The new tally.
        """

    def accept_model(self, model):
        """
        Determines whether the Bucket accepts updates from the given model.

        @param model: Class Model of the updated instance.
        @return: bool       Indicates if the model is accepted or not.
        """
        return True

    def update_tally(self, old_tally, new_tally):
        """
        Handles updating the tally.

        @param old_tally: The current tally.
        @param new_tally: The new updated tally.
        """
        self.tally = new_tally

    def __init__(self):
        self.tally = self.get_tally()

    def handle(self, model, old_data, new_data):
        """
        Handle update to model instance.

        @param model: Class      Model of the updated instance.
        @param old_data: Mapping Old data of the model.
        @param new_data: Mapping New data of the model.
        """
        if not self.accept_model(model):
            return

        if old_data is None:
            if new_data is None:
                raise ValueError('old_data and new_data cannot both be None')
            else:
                event = self.handle_create(model, new_data)
        else:
            if new_data is None:
                event = self.handle_delete(model, old_data)
            else:
                event = self.handle_update(model, old_data, new_data)

        if event is None:
            return

        new_tally = self.handle_event(self.tally, event)
        self.update_tally(self.tally, new_tally)

    def listen(self, base_class=models.Model):
        """
        Start listening to updates for all instances of base_class or any of
        its subclasses.

        @param base_class: Class Model to listen for updates on.
        """
        if not (
            base_class is models.Model or
            (
                hasattr(base_class, 'Meta') and
                getattr(base_class.Meta, 'abstract', False)
            )
        ):
            model_data = {}

            @receiver(post_init, sender=base_class, weak=False)
            def handle_post_init(sender, instance, **kwargs):
                model_data[instance.pk] = model_instance_to_dict(instance)

            @receiver(post_save, sender=base_class, weak=False)
            def handle_post_save(sender, instance, created, **kwargs):
                model_data[instance.pk] = model_instance_to_dict(instance)
                if created:
                    old_data = None
                else:
                    old_data = model_data[instance.pk]
                new_data = model_instance_to_dict(instance)
                self.handle(base_class, old_data, new_data)
                model_data[instance.pk] = new_data

            @receiver(post_delete, sender=base_class, weak=False)
            def handle_post_delete(sender, instance, **kwargs):
                self.handle(base_class, model_data[instance.pk], None)
                del model_data[instance.pk]

        for subclass in base_class.__subclasses__():
            self.listen(subclass)
