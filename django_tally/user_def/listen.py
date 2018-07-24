from django.db.models import Model
from django.db.models.signals import post_save, post_delete

from ..subscription import Subscription
from .tally import UserDefTallyBase
from .group_tally import UserDefGroupTallyBase


DEFAULT_TALLIES = (UserDefTallyBase, UserDefGroupTallyBase)


class TallySubscription(Subscription):
    """
    Special subscription class that handles the listening of user defined
    tallies.
    """

    def __init__(self, senders, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._senders = senders
        self._active_tallies = {}

    def _open_tally(self, tally):
        self._active_tallies[tally] = tally.listen(*self._senders)

    def _close_tally(self, tally):
        if tally in self._active_tallies:
            self._active_tallies.pop(tally).close()

    def handle_post_save(self, sender, instance, **args):
        if instance in self._active_tallies:
            old = next(
                ins
                for ins, _ in self._active_tallies.items()
                if ins == instance
            )
            instance._Tally__model_data = old._Tally__model_data
            self._close_tally(old)
            self._open_tally(instance)

    def handle_post_delete(self, sender, instance, **args):
        self._close_tally(instance)

    def open(self):
        super().open()
        for signal, handler, sender in self._receivers:
            if signal == post_save and handler == self.handle_post_save:
                for instance in sender.objects.all():
                    self._open_tally(instance)

    def close(self):
        for instance in list(self._active_tallies):
            self._close_tally(instance)
        super().close()


def on(*senders, tallies=DEFAULT_TALLIES, sub=None):
    """
    Creates a subscription of certain user defined tally classes on certain
    senders.

    @param senders: [Class]
        The senders to listen on.
    @param tallies: [Class]
        The user defined tally classes to listen for.
    @param sub: TallySubscription
        An existing subscription to add the listeners to, if None the function
        will create a new subscription.
    @return: TallySubscription
        The subscription that the listeners were added to.
    """
    if sub is None:
        sub = TallySubscription(senders)

    for tally in tallies:
        if tally is not Model and not (
            hasattr(tally, '_meta') and
            getattr(tally._meta, 'abstract', False)
        ):
            sub.add(post_save, sub.handle_post_save, tally)
            sub.add(post_delete, sub.handle_post_delete, tally)

        on(senders, tallies=tally.__subclasses__(), sub=sub)

    return sub


def listen(*senders, tallies=DEFAULT_TALLIES, sub=None):
    """
    Creates a subscription of certain user defined tally classes on certain
    senders and opens it.

    @param senders: [Class]
        The senders to listen on.
    @param tallies: [Class]
        The user defined tally classes to listen for.
    @param sub: TallySubscription
        An existing subscription to add the listeners to, if None the function
        will create a new subscription.
    @return: TallySubscription
        The subscription that the listeners were added to.
    """
    sub = on(*senders, tallies=tallies, sub=sub)
    sub.open()
    return sub
