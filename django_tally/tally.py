from abc import ABC, abstractmethod

from django.db import models
from django.db.models.signals import post_init, post_save, post_delete


def model_instance_to_dict(instance):
    """
    Converts a Django model instance to a dict of values for all it's concrete
    non many to many fields.

    @param instance: Model
        The model instance to convert.
    @return: dict
        The generated dict of values.
    """
    res = {}

    for field in instance._meta.get_fields():
        if not field.concrete or field.many_to_many:
            continue

        if isinstance(field, models.ForeignKey):
            value = getattr(instance, field.name + '_id')
        elif isinstance(field, models.FileField):
            value = getattr(instance, field.name).name
        else:
            value = getattr(instance, field.name)

        res[field.name] = value

    return res


class Tally(ABC):
    """
    Abstract base class for a Tally.
    A tally is a container that keeps track of a tally and updates this tally
    based on changes happening to model instances.
    """

    @abstractmethod
    def get_tally(self):
        """
        Get initial value for the tally.

        @return: Any
            Initial value for the tally.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_create(self, model, data):
        """
        Get event based on creation of model instance.

        @param model: Class
            Model of the updated instance.
        @param data: Mapping
            New data of the model.
        @return: Any
            Event triggered by the update.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_update(self, model, old_data, new_data):
        """
        Get event based on update to model instance.

        @param model: Class
            Model of the updated instance.
        @param old_data: Mapping
            Old data of the model.
        @param new_data: Mapping
            New data of the model.
        @return: Any
            Event triggered by the update.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_delete(self, model, data):
        """
        Get event based on delete to model instance.

        @param model: Class
            Model of the updated instance.
        @param data: Mapping
            Old data of the model.
        @return: Any
            Event triggered by the delete.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_event(self, tally, event):
        """
        Update tally based on event.

        @param tally: Any
            The current tally.
        @param event: Any
            Event triggered.
        @return: Any
            The new tally.
        """
        raise NotImplementedError

    def update_tally(self, old_tally, new_tally):
        """
        Handles updating the tally.

        @param old_tally: Any
            The current tally.
        @param new_tally: Any
            The new updated tally.
        """
        self.tally = new_tally

    def __init__(self):
        """
        Initialize Tally.
        """
        self.tally = self.get_tally()
        self.__model_data = {}

    def handle(self, model, old_data, new_data):
        """
        Handle update to model instance.

        @param model: Class
            Model of the updated instance.
        @param old_data: Mapping
            Old data of the model.
        @param new_data: Mapping
            New data of the model.
        """
        assert not (old_data is None and new_data is None), (
            'old_data and new_data cannot both be None'
        )

        if old_data is None:
            event = self.handle_create(model, new_data)
        elif new_data is None:
            event = self.handle_delete(model, old_data)
        else:
            event = self.handle_update(model, old_data, new_data)

        if event is None:
            return

        new_tally = self.handle_event(self.tally, event)
        self.update_tally(self.tally, new_tally)

    def _handle_post_init(self, sender, instance, **kwargs):
        """
        Handle post_init signal from a connected model.

        @param sender: Class
            Model that sent the event.
        @param instance: sender
            Instance that was initialized.
        @param kwargs: Mapping
            Remaining keyword arguments.
        """
        self.__model_data[instance.pk] = model_instance_to_dict(instance)

    def _handle_post_save(self, sender, instance, created, **kwargs):
        """
        Handle post_save signal from a connected model.

        @param sender: Class
            Model that sent the event.
        @param instance: sender
            Instance that was saved.
        @param created: bool
            If the instance was created with this save.
        @param kwargs: Mapping
            Remaining keyword arguments.
        """
        if created:
            old_data = None
        else:
            old_data = self.__model_data[instance.pk]
        new_data = model_instance_to_dict(instance)
        self.handle(sender, old_data, new_data)
        self.__model_data[instance.pk] = new_data

    def _handle_post_delete(self, sender, instance, **kwargs):
        """
        Handle post_delete signal from a connected model.

        @param sender: Class
            Model that sent the event.
        @param instance: sender
            Instance that was deleted.
        @param kwargs: Mapping
            Remaining keyword arguments.
        """
        self.handle(sender, self.__model_data[instance.pk], None)
        del self.__model_data[instance.pk]

    def subscribe(self, sender=models.Model, sub=None):
        """
        Create a subscription to signals from a certain sender and it's
        subclasses.

        @param sender: Class
            Sender to subscribe to.
        @param sub: Tally.Subscription
            Existing subscription to extend. If given None the method will
            create a new subscription object.
        @return: Tally.Subscription
            Subscription object representing the subscribed signals.
        """
        if sub is None:
            sub = Tally.Subscription()

        if sender is not models.Model and not (
            hasattr(sender, 'Meta') and
            getattr(sender.Meta, 'abstract', False)
        ):
            sub.add(post_init, self._handle_post_init, sender)
            sub.add(post_save, self._handle_post_save, sender)
            sub.add(post_delete, self._handle_post_delete, sender)

        for subclass in sender.__subclasses__():
            self.subscribe(subclass, sub)

        return sub

    def listen(self, base_class=models.Model, sub=None):
        """
        Create a subscription to signals from a certain sender and it's
        subclasses and open it.

        @param sender: Class
            Sender to subscribe to.
        @param sub: Tally.Subscription
            Existing subscription to extend. If given None the method will
            create a new subscription object.
        @return: Tally.Subscription
            Subscription object representing the subscribed signals.
        """
        sub = self.subscribe(base_class, sub)
        sub.open()
        return sub

    class Subscription:
        """
        Represents a subscription between tallies and models. A Subscription
        object can also be used as a context manager that opens and closes the
        subscription.
        """

        def __init__(self, receivers=None):
            """
            Initialize Subscription.

            @param receivers: Set[(Signal, Function, Class)]
                A set of receivers that the subscription contains. A receiver
                is represented by a three tuple of the signal to receive, the
                function to handle this signal, and the class to use as sender.
            """
            if receivers is None:
                receivers = set()

            self.connected = False
            self.__receivers = receivers

        def add(self, signal, handler, sender):
            """
            Add a receiver to the subscription.

            @param signal: Signal
                The signal to receive.
            @param handler: Function
                The function that handles the signal.
            @param sender: Class
                The class to use as sender.
            """
            assert not self.connected, 'Can only add receiver while closed'
            self.__receivers.add((signal, handler, sender))

        def open(self):
            """
            Opens the subscription.
            """
            assert not self.connected, 'Connection is already open'
            self.connected = True
            for signal, handler, sender in self.__receivers:
                signal.connect(handler, sender=sender)

        def close(self):
            """
            Closes the subscription.
            """
            assert self.connected, 'Connection is already closed'
            self.connected = False
            for signal, handler, sender in self.__receivers:
                signal.disconnect(handler, sender=sender)

        def __enter__(self):
            """
            Entry method for using the model as context manager. This method
            opens the subscription.
            """
            return self.open()

        def __exit__(self, type, value, traceback):
            """
            Exit method for using the model as context manager. This method
            closes the subscription.

            @param type: Class
                Type of the exception thrown or None when exited normally.
            @param value: Exception
                The exception thrown or None when exited normally.
            @param traceback: Traceback
                The traceback of the exception thrown or None when exited
                normally.
            @return: bool
                Whether to suppress the thrown exception.
            """
            self.close()
            return False
