"""
This module implements a collector for the VBA language.
"""
from pathlib import Path

from mkdocstrings.handlers.base import BaseCollector

from mkdocstrings_handlers.vba.types import VbaModuleInfo
from mkdocstrings_handlers.vba.util import (
    collapse_long_lines,
    find_file_docstring,
    find_procedures,
)


class VbaCollector(BaseCollector):
    """
    Collect data from a VBA file.
    """

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
