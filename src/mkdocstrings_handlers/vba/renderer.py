"""
This module implements a renderer for the VBA language.

Most of this is just copied / hacked together from the Python renderer.
"""

from __future__ import annotations

import enum
import re
import sys
from collections import ChainMap
from typing import Any, Sequence

from griffe.dataclasses import Alias, Object
from markdown import Markdown
from markupsafe import Markup
from mkdocstrings.extension import PluginError
from mkdocstrings.handlers.base import BaseRenderer, CollectorItem
from mkdocstrings.loggers import get_logger

from mkdocstrings_handlers.vba.types import VbaModuleInfo

logger = get_logger(__name__)


class Order(enum.Enum):
    """Enumeration for the possible members ordering."""

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


class VbaRenderer(BaseRenderer):
    """The class responsible for loading Jinja templates and rendering them.

    It defines some configuration options, implements the `render` method,
    and overrides the `update_env` method of the [`BaseRenderer` class][mkdocstrings.handlers.base.BaseRenderer].
    """

    fallback_theme = "material"
    """
    The theme to fall back to.
    """

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
        "members_order": Order.alphabetical.value,
        "docstring_section_style": "table",
    }
    """The default rendering options.
    
    See [`default_config`][mkdocstrings_handlers.vba.renderer.VbaRenderer.default_config].

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
    **`members_order`** | `str` | The members ordering to use. Options: `alphabetical` - order by the members names, `source` - order members as they appear in the source file. | `alphabetical`
    **`docstring_section_style`** | `str` | The style used to render docstring sections. Options: `table`, `list`, `spacy`. | `table`
    """  # noqa: E501

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
        try:
            final_config["members_order"] = Order(final_config["members_order"])
        except ValueError:
            choices = "', '".join(item.value for item in Order)
            raise PluginError(
                f"Unknown members_order '{final_config['members_order']}', choose between '{choices}'."
            )

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
        self.env.filters["crossref"] = self.do_crossref
        self.env.filters["multi_crossref"] = self.do_multi_crossref
        self.env.filters["order_members"] = self.do_order_members

    @staticmethod
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

    @staticmethod
    def do_crossref(path: str, brief: bool = True) -> Markup:
        """Filter to create cross-references.

        Parameters:
            path: The path to link to.
            brief: Show only the last part of the path, add full path as hover.

        Returns:
            Markup text.
        """
        full_path = path
        if brief:
            path = full_path.split(".")[-1]
        return Markup(
            "<span data-autorefs-optional-hover={full_path}>{path}</span>"
        ).format(full_path=full_path, path=path)

    @staticmethod
    def do_multi_crossref(text: str, code: bool = True) -> Markup:
        """Filter to create cross-references.

        Parameters:
            text: The text to scan.
            code: Whether to wrap the result in a code tag.

        Returns:
            Markup text.
        """
        group_number = 0
        variables = {}

        def repl(match):  # noqa: WPS430
            nonlocal group_number  # noqa: WPS420
            group_number += 1
            path = match.group()
            path_var = f"path{group_number}"
            variables[path_var] = path
            return f"<span data-autorefs-optional-hover={{{path_var}}}>{{{path_var}}}</span>"

        text = re.sub(r"([\w.]+)", repl, text)
        if code:
            text = f"<code>{text}</code>"
        return Markup(text).format(**variables)
