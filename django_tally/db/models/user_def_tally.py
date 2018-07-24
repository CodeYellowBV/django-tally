from django.db.models import Model

from .user_def_tally_base import get_user_def_tally_base


def get_user_def_tally(base_class=Model):
    """
    Creates a user def tally class for a certain base class.

    @param base_class: Class
        The base class to base the returned class on. Defaults to
        django.db.models.Model.
    @return: Class
        The generated base class.
    """

    UserDefTallyBase = get_user_def_tally_base(base_class)

    class UserDefTally(UserDefTallyBase):
        pass

    return UserDefTally


UserDefTally = get_user_def_tally()
