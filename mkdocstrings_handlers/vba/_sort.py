from __future__ import annotations

import enum
import sys
from typing import Any, Sequence

from griffe.dataclasses import Alias, Object
from mkdocstrings.handlers.base import CollectorItem


class Order(enum.Enum):
    """
    Enumeration for the possible members ordering.
    """

    alphabetical = "alphabetical"
    source = "source"


def _sort_key_alphabetical(item: CollectorItem) -> Any:
    # chr(sys.maxunicode) is a string that contains the final unicode
    # character, so if 'name' isn't found on the object, the item will go to
    # the end of the list.
    return item.name or chr(sys.maxunicode)


def _sort_key_source(item: CollectorItem) -> Any:
    # if 'lineno' is none, the item will go to the start of the list.
    return item.lineno if item.lineno is not None else -1


order_map = {
    Order.alphabetical: _sort_key_alphabetical,
    Order.source: _sort_key_source,
}


def do_order_members(
    members: Sequence[Object | Alias], order: Order
) -> Sequence[Object | Alias]:
    """Order members given an ordering method.

    Parameters:
        members: The members to order.
        order: The ordering method.

    Returns:
        The same members, ordered.
    """
    return sorted(members, key=order_map[order])
