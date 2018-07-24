from .user_def_tally import get_user_def_tally
from .user_def_group_tally import get_user_def_group_tally


UserDefTally = get_user_def_tally()
UserDefGroupTally = get_user_def_group_tally()


__all__ = [UserDefTally, UserDefGroupTally]
