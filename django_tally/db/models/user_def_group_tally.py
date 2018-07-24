from django.db.models import Model

from .user_def_group_tally_base import get_user_def_group_tally_base


def get_user_def_group_tally(base_class=Model):
    """
    Creates a user def group tally class for a certain base class.

    @param base_class: Class
        The base class to base the returned class on. Defaults to
        django.db.models.Model.
    @return: Class
        The generated base class.
    """

    UserDefGroupTallyBase = get_user_def_group_tally_base(base_class)

    class UserDefGroupTally(UserDefGroupTallyBase):
        pass

    return UserDefGroupTally


UserDefGroupTally = get_user_def_group_tally()
