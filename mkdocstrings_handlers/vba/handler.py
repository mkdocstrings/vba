"""This module implements a handler for the VBA language."""

import posixpath
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Optional, Tuple

from griffe.logger import patch_loggers
from mkdocstrings.handlers.base import BaseHandler
from mkdocstrings.inventory import Inventory
from mkdocstrings.loggers import get_logger

from mkdocstrings_handlers.vba.collector import VbaCollector
from mkdocstrings_handlers.vba.renderer import VbaRenderer

patch_loggers(get_logger)


class VbaHandler(BaseHandler):
    """The Vba handler class."""

    domain: str = "vba"
    """The cross-documentation domain/language for this handler."""

    enable_inventory: bool = True
    """Whether this handler is interested in enabling the creation of the `objects.inv` Sphinx inventory file."""

    @classmethod
    def load_inventory(
        cls,
        in_file: BinaryIO,
        url: str,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Tuple[str, str]]:
        """Yield items and their URLs from an inventory file streamed from `in_file`.

        This implements mkdocstrings' `load_inventory` "protocol" (see plugin.py).

        Arguments:
            in_file: The binary file-like object to read the inventory from.
            url: The URL that this file is being streamed from (used to guess `base_url`).
            base_url: The URL that this inventory's sub-paths are relative to.
            **kwargs: Ignore additional arguments passed from the config.

        Yields:
            Tuples of (item identifier, item URL).
        """
        if base_url is None:
            base_url = posixpath.dirname(url)

        for item in Inventory.parse_sphinx(in_file, domain_filter=("py",)).values():
            yield item.name, posixpath.join(base_url, item.uri)


def get_handler(
    theme: str,
    custom_templates: Optional[str] = None,
    **config: Any,
) -> VbaHandler:
    """Simply return an instance of `VbaHandler`.

    Arguments:
        theme: The theme to use when rendering contents.
        custom_templates: Directory containing custom templates.
        **config: Configuration passed to the handler.

    Returns:
        An instance of `VbaHandler`.
    """
    return VbaHandler(
        # TODO How do we get the path of the directory containing mkdocs.yml here?
        #  Indentifiers for .bas files need to be found relative to that.
        collector=VbaCollector(base_dir=Path(".")),
        renderer=VbaRenderer("vba", theme, custom_templates),
    )
