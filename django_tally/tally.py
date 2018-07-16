from copy import deepcopy
from collections import defaultdict

from django.db import models
from django.db.models.signals import post_init, post_save, post_delete


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
        if created:
            old_value = None
        else:
            old_value = self.__model_data[type(instance)][instance.pk]
        new_value = self.get_value(instance)
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
        self._handle(self.__model_data[type(instance)][instance.pk], None)
        del self.__model_data[type(instance)][instance.pk]

    def __call__(self, *senders, sub=None):
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
            sub = Tally.Subscription()

        for sender in senders:
            if sender is not models.Model and not (
                hasattr(sender, 'Meta') and
                getattr(sender.Meta, 'abstract', False)
            ):
                sub.add(post_init, self._handle_post_init, sender)
                sub.add(post_save, self._handle_post_save, sender)
                sub.add(post_delete, self._handle_post_delete, sender)

            for subclass in sender.__subclasses__():
                self(subclass, sub=sub)

        return sub

    def listen(self, *senders, sub=None):
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
        sub = self(*senders, sub=sub)
        sub.open()
        return sub

    def reset(self):
        """
        Resets the tally to it's original value.
        """
        self.tally = self.get_tally()

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

        def __call__(self, func):
            """
            Wraps the given function to open this subscription right before it
            is called and close right after the call is done.

            @param func: Function
                The function to wrap.
            @return:
                The wrapped version of the function.
            """
            def res(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return res
