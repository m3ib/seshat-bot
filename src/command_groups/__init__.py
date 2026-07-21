"""Command groups used in the app."""

from .admin_group import AdminGroup
from .list_group import ListGroup
from .show_group import ShowGroup

CMD_GROUPS = [AdminGroup, ShowGroup]
