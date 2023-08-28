"""This module implements a handler for the VBA language."""

from __future__ import annotations

import posixpath
from collections import ChainMap
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Optional, Tuple

from griffe.logger import patch_loggers
from markdown import Markdown
from mkdocstrings.handlers.base import BaseHandler
from mkdocstrings.inventory import Inventory
from mkdocstrings.loggers import get_logger

from mkdocstrings_handlers.vba.types import VbaModuleInfo
from mkdocstrings_handlers.vba.util import (
    collapse_long_lines,
    find_file_docstring,
    find_procedures,
)

patch_loggers(get_logger)


class VbaHandler(BaseHandler):
    """The Vba handler class."""

    domain: str = "vba"
    """The cross-documentation domain/language for this handler."""

    enable_inventory: bool = True
    """Whether this handler is interested in enabling the creation of the `objects.inv` Sphinx inventory file."""

    fallback_theme = "material"
    """The theme to fall back to."""

    default_config: dict = {
        "show_root_heading": False,
        "show_root_toc_entry": True,
        "show_root_full_path": True,
        "show_root_members_full_path": False,
        "show_object_full_path": False,
        "show_category_heading": False,
        "show_if_no_docstring": False,
        "show_signature": True,
        "separate_signature": False,
        "line_length": 60,
        "show_source": True,
        "show_bases": True,
        "show_submodules": True,
        "heading_level": 2,
        "docstring_section_style": "table",
    }
    """The default rendering options.
    
    See [`default_config`][mkdocstrings_handlers.vba.handler.VbaHandler.default_config].

    Option | Type | Description | Default
    ------ | ---- | ----------- | -------
    **`show_root_heading`** | `bool` | Show the heading of the object at the root of the documentation tree. | `False`
    **`show_root_toc_entry`** | `bool` | If the root heading is not shown, at least add a ToC entry for it. | `True`
    **`show_root_full_path`** | `bool` | Show the full VBA path for the root object heading. | `True`
    **`show_object_full_path`** | `bool` | Show the full VBA path of every object. | `False`
    **`show_root_members_full_path`** | `bool` | Show the full VBA path of objects that are children of the root object (for example, classes in a module). When False, `show_object_full_path` overrides. | `False`
    **`show_category_heading`** | `bool` | When grouped by categories, show a heading for each category. | `False`
    **`show_if_no_docstring`** | `bool` | Show the object heading even if it has no docstring or children with docstrings. | `False`
    **`show_signature`** | `bool` | Show method and function signatures. | `True`
    **`separate_signature`** | `bool` | Whether to put the whole signature in a code block below the heading. | `False`
    **`line_length`** | `int` | Maximum line length when formatting code. | `60`
    **`show_source`** | `bool` | Show the source code of this object. | `True`
    **`show_bases`** | `bool` | Show the base classes of a class. | `True`
    **`show_submodules`** | `bool` | When rendering a module, show its submodules recursively. | `True`
    **`heading_level`** | `int` | The initial heading level to use. | `2`
    **`docstring_section_style`** | `str` | The style used to render docstring sections. Options: `table`, `list`, `spacy`. | `table`
    """  # noqa: E501

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

    def collect(
        self,
        identifier: str,
        config: dict,
    ) -> VbaModuleInfo:
        """Collect the documentation tree given an identifier and selection options.

        Arguments:
            identifier: Which VBA file (.bas or .cls) to collect from.
            config: Selection options, used to alter the data collection.

        Raises:
            CollectionError: When there was a problem collecting the documentation.

        Returns:
            The collected object tree.
        """
        p = Path(identifier)
        with p.open("r") as f:
            code = f.read()

        code = collapse_long_lines(code)

        return VbaModuleInfo(
            docstring=find_file_docstring(code),
            source=code.splitlines(),
            path=p,
            procedures=list(find_procedures(code)),
        )

    def render(
        self,
        data: VbaModuleInfo,
        config: dict,
    ) -> str:
        final_config = ChainMap(config, self.default_config)
        render_type = "module"

        template = self.env.get_template(f"{render_type}.html")

        # Heading level is a "state" variable, that will change at each step
        # of the rendering recursion. Therefore, it's easier to use it as a plain value
        # than as an item in a dictionary.
        heading_level = final_config["heading_level"]

        return template.render(
            **{
                "config": final_config,
                render_type: data,
                "heading_level": heading_level,
                "root": True,
            },
        )

    def get_anchors(self, data: VbaModuleInfo) -> list[str]:
        return list(
            {data.path.as_posix(), *(p.signature.name for p in data.procedures)}
        )

    def update_env(self, md: Markdown, config: dict) -> None:
        super().update_env(md, config)
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False



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
    return VbaHandler("vba", theme, custom_templates)
