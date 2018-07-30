from copy import deepcopy
from collections import defaultdict

from django.db import models
from django.db.models.signals import post_init, post_save, post_delete

from .subscription import Subscription


class Tally:
    """
    Base class for a Tally.
    A tally is a container that keeps track of a tally and updates this tally
    based on changes happening to model instances.
    """

    def get_tally(self):
        """
        Get initial value for the tally.

        @return: Any
            Initial value for the tally.
        """
        raise NotImplementedError

    def get_value(self, instance):
        """
        Get value of a model instance to be used in changes.

        @param model: Any
            Instance to get the value of.
        @return: Any
            Value of model instance.
        """
        return deepcopy(instance)

    def handle_change(self, tally, old_value, new_value):
        """
        Change tally based on a change to a model instance.

        @param tally: Any
            Current value of the tally.
        @param old_value: Any
            Old value of the model.
        @param new_value: Any
            New value of the model.
        @return: Any
            New tally value.
        """
        raise NotImplementedError

    def __init__(self, *args):
        """
        Initialize Tally.
        """
        if len(args) > 1:
            raise TypeError(
                '{}.__init__() takes at most 1 argument ({} given)'
                .format(type(self).__name__, args)
            )
        elif len(args) == 1:
            self.tally = args[0]
        else:
            self.tally = self.get_tally()

        self.__model_data = defaultdict(dict)

    def _handle(self, old_value, new_value):
        """
        Handle update to model instance.

        @param old_value: Any
            Old value of the model.
        @param new_value: Mapping
            New value of the model.
        """
        if old_value is None and new_value is None:
            return

        self.tally = self.handle_change(self.tally, old_value, new_value)

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
        if instance.pk is None:
            return
        self.__model_data[type(instance)][instance.pk] = (
            self.get_value(instance)
        )

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
        new_value = self.get_value(instance)
        if created:
            old_value = None
        elif instance.pk in self.__model_data[type(instance)]:
            old_value = self.__model_data[type(instance)][instance.pk]
        else:
            self.__model_data[type(instance)][instance.pk] = new_value
            return
        self._handle(old_value, new_value)
        self.__model_data[type(instance)][instance.pk] = new_value

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
        if instance.pk not in self.__model_data[type(instance)]:
            return
        self._handle(self.__model_data[type(instance)][instance.pk], None)
        del self.__model_data[type(instance)][instance.pk]

    def on(self, *senders, sub=None):
        """
        Create a subscription to signals from certain senders and their
        subclasses.

        @param *senders: Class[]
            Senders to subscribe to.
        @param sub: Tally.Subscription
            Existing subscription to extend. If given None the method will
            create a new subscription object.
        @return: Tally.Subscription
            Subscription object representing the subscribed signals.
        """
        if sub is None:
            sub = Subscription()

        for sender in senders:
            if sender is not models.Model and not (
                hasattr(sender, '_meta') and
                getattr(sender._meta, 'abstract', False)
            ):
                sub.add(post_init, self._handle_post_init, sender)
                sub.add(post_save, self._handle_post_save, sender)
                sub.add(post_delete, self._handle_post_delete, sender)

            for subclass in sender.__subclasses__():
                self.on(subclass, sub=sub)

        return sub

    def listen(self, *args, **kwargs):
        """
        Create a subscription to signals from certain senders and their
        subclasses and open it.

        @param *senders: Class[]
            Senders to subscribe to.
        @param sub: Tally.Subscription
            Existing subscription to extend. If given None the method will
            create a new subscription object.
        @return: Tally.Subscription
            Subscription object representing the subscribed signals.
        """
        sub = self.on(*args, **kwargs)
        sub.open()
        return sub

    def reset(self):
        """
        Resets the tally to it's original value.
        """
        self.tally = self.get_tally()
