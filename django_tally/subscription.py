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
        self._receivers = receivers

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
        self._receivers.add((signal, handler, sender))

    def open(self):
        """
        Opens the subscription.
        """
        assert not self.connected, 'Connection is already open'
        self.connected = True
        for signal, handler, sender in self._receivers:
            signal.connect(handler, sender=sender, weak=False)

    def close(self):
        """
        Closes the subscription.
        """
        assert self.connected, 'Connection is already closed'
        self.connected = False
        for signal, handler, sender in self._receivers:
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
