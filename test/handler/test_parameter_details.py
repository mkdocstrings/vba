"""
Test parameter defaults and modifiers in generated documentation.
"""

import re
import unittest
from html import unescape
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocs.commands.build import build
from mkdocs.config import load_config

from test.helpers import assert_no_warnings


class TestParameterDetails(unittest.TestCase):
    """
    Show useful parameter information in table and list section styles.
    """

    def test_modifiers_and_defaults(self) -> None:
        """
        Match differently cased names and display authored modifiers and literal defaults.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "source.bas").write_text(
                'Sub useValues(ByVal value As String, Optional ByRef fallback As String = "a&b")\n'
                "    ' Use values.\n    '\n    ' Args:\n"
                "    '     VALUE: The value.\n    '     FALLBACK: The fallback.\nEnd Sub\n"
                "Sub useItems(ParamArray items() As Variant)\n"
                "    ' Use items.\n    '\n    ' Args:\n    '     ITEMS: The items.\nEnd Sub\n",
                encoding="utf-8",
            )
            for style in ("table", "list", "spacy"):
                (root / "docs" / f"{style}.md").write_text(
                    "# Reference\n\n::: source.bas\n    handler: vba\n    options:\n"
                    "      show_source: false\n      show_signature: false\n"
                    f"      docstring_section_style: {style}\n",
                    encoding="utf-8",
                )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Parameters\nuse_directory_urls: false\n", encoding="utf-8"
            )
            with assert_no_warnings():
                build(
                    config=load_config(
                        config_file=str(config_file), plugins=["mkdocstrings"]
                    )
                )
            for style in ("table", "list", "spacy"):
                html = (root / "site" / f"{style}.html").read_text(encoding="utf-8")
                text = " ".join(unescape(re.sub(r"<[^>]+>", "", html)).split())
                self.assertIn('"a&b"', text)
                self.assertNotIn("TODO", text)
                self.assertNotIn("&amp;", text)
                if style == "table":
                    self.assertIn("ByVal", text)
                    self.assertIn("Optional ByRef", text)
                    self.assertIn("ParamArray", text)
                if style == "list":
                    self.assertIn('default: "a&b"', text)
