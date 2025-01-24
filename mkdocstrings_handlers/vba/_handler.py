"""
This module implements a handler for the VBA language.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import (
    Any,
    MutableMapping,
    Dict,
    Mapping,
    Tuple,
)

from griffe import patch_loggers
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocstrings import BaseHandler, CollectionError
from mkdocstrings.loggers import get_logger

from ._crossref import do_crossref, do_multi_crossref
from ._sort import Order, do_order_members
from ._types import VbaModuleInfo
from ._util import find_file_docstring, collapse_long_lines, find_procedures

patch_loggers(get_logger)


class VbaHandler(BaseHandler):
    """
    The VBA handler class.
    """

    base_dir: Path
    """
    The directory in which to look for VBA files.
    """

    encoding: str
    """
    The encoding to use when reading VBA files.
    Excel exports .bas and .cls files as `latin1`.
    See https://en.wikipedia.org/wiki/ISO/IEC_8859-1 .
    """

    def __init__(self, *, base_dir: Path, encoding: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_dir = base_dir
        self.encoding = encoding

    name: str = "vba"  # type: ignore[misc]
    """
    The handler's name.
    """

    domain: str = "vba"  # type: ignore[misc]
    """
    The cross-documentation domain/language for this handler.
    """

    fallback_theme = "material"
    """
    The theme to fall back to.
    """

    default_config = {
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
    """
    The default handler configuration.

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
    """

    def get_options(self, local_options: Mapping[str, Any]) -> Dict[str, Any]:
        """Combine the default options with the local options.

        Arguments:
            local_options: The options provided in Markdown pages.

        Returns:
            The combined options.
        """
        return deepcopy({**self.default_config, **local_options})

    def collect(
        self,
        identifier: str,
        config: MutableMapping[str, Any],
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
        p = Path(self.base_dir, identifier)
        if not p.exists():
            raise CollectionError("File not found.")

        code = p.read_text(encoding=self.encoding, errors="replace")
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
        options: MutableMapping[str, Any],
        *,
        locale: str | None = None,
    ) -> str:
        template = self.env.get_template(f"module.html")

        # Heading level is a "state" variable, that will change at each step
        # of the rendering recursion. Therefore, it's easier to use it as a plain value
        # than as an item in a dictionary.
        heading_level = options["heading_level"]
        try:
            options["members_order"] = Order(options["members_order"])
        except ValueError:
            choices = "', '".join(item.value for item in Order)
            raise PluginError(
                f"Unknown members_order '{options['members_order']}', choose between '{choices}'."
            )

        return template.render(
            config=options,
            module=data,
            heading_level=heading_level,
            root=True,
        )

    def update_env(self, config: Dict[Any, Any]) -> None:
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False
        self.env.filters["crossref"] = do_crossref
        self.env.filters["multi_crossref"] = do_multi_crossref
        self.env.filters["order_members"] = do_order_members

    def get_aliases(self, identifier: str) -> Tuple[str, ...]:
        """Get the aliases of the given identifier.

        Aliases are used to register secondary URLs in mkdocs-autorefs,
        to make sure cross-references work with any location of the same object.

        Arguments:
            identifier: The identifier to get aliases for.

        Returns:
            A tuple of aliases for the given identifier.
        """
        try:
            data = self.collect(identifier, {})
        except CollectionError:
            return ()
        return data.path.as_posix(), *(p.signature.name for p in data.procedures)


def get_handler(
    *,
    encoding: str = "latin1",
    tool_config: MkDocsConfig | None = None,
    **kwargs: Any,
) -> VbaHandler:
    """
    Get a new `VbaHandler`.

    Arguments:
        encoding:
            The encoding to use when reading VBA files.
            Excel exports .bas and .cls files as `latin1`.
            See https://en.wikipedia.org/wiki/ISO/IEC_8859-1 .
        tool_config: SSG configuration.
        kwargs: Extra keyword arguments that we don't use.

    Returns:
        An instance of `VbaHandler`.
    """
    base_dir = (
        Path(getattr(tool_config, "config_file_path", None) or "./mkdocs.yml")
        .resolve()
        .parent
    )
    return VbaHandler(base_dir=base_dir, encoding=encoding, **kwargs)
