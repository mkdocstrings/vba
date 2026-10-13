"""
Test rendering option errors and shortened module headings.
"""

import unittest
import re
from html import unescape
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import PluginError

from mkdocstrings_handlers.vba import get_handler
from test.helpers import assert_no_warnings


class TestOptionValidation(unittest.TestCase):
    """
    Reject invalid built-in settings without restricting custom template options.
    """

    def test_invalid_values(self) -> None:
        """
        Report invalid settings before they hide documentation or break template rendering.
        """
        for name, invalid in (
            ("docstring_section_style", "typo"),
            ("docstring_section_style", None),
            ("members_order", "random"),
            ("heading_level", "three"),
            ("heading_level", False),
            ("heading_level", 0),
            ("line_length", -1),
            ("line_length", 60.5),
            ("show_source", "false"),
            ("show_signature", 1),
        ):
            with self.subTest(name=name, value=invalid):
                for global_setting in (True, False):
                    handler = get_handler(
                        handler_config=(
                            {"options": {name: invalid}} if global_setting else {}
                        )
                    )
                    with self.assertRaisesRegex(PluginError, name):
                        handler.get_options({} if global_setting else {name: invalid})

    def test_override_and_custom_options(self) -> None:
        """
        Validate the combined options and preserve arbitrary custom-template data.
        """
        handler = get_handler(handler_config={"options": {"line_length": 0}})
        options = handler.get_options({"line_length": 80, "custom": {"label": "value"}})
        self.assertEqual(80, options["line_length"])
        self.assertEqual({"label": "value"}, options["custom"])
        for style in ("table", "list", "spacy"):
            self.assertEqual(
                style,
                get_handler().get_options({"docstring_section_style": style})[
                    "docstring_section_style"
                ],
            )

    def test_module_headings(self) -> None:
        """
        Shorten the displayed module name without changing its source path or anchor.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            source = root / "source.bas"
            source.write_text("' Module documentation.\n", encoding="utf-8")
            for name, full_path in (("full", True), ("short", False)):
                (root / "docs" / f"{name}.md").write_text(
                    "# Reference\n\n::: source.bas\n    handler: vba\n    options:\n"
                    "      show_root_heading: true\n"
                    f"      show_root_full_path: {str(full_path).lower()}\n",
                    encoding="utf-8",
                )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Headings\nuse_directory_urls: false\n", encoding="utf-8"
            )
            with assert_no_warnings():
                build(
                    config=load_config(
                        config_file=str(config_file), plugins=["mkdocstrings"]
                    )
                )
            for name, expected in (
                ("full", source.as_posix()),
                ("short", "source.bas"),
            ):
                html = (root / "site" / f"{name}.html").read_text(encoding="utf-8")
                heading = re.search(
                    r'<h2\b[^>]*id="'
                    + re.escape(source.as_posix())
                    + r'"[^>]*>(.*?)</h2>',
                    html,
                    re.DOTALL,
                )
                assert heading is not None
                self.assertEqual(
                    expected, unescape(re.sub(r"<[^>]+>", "", heading[1])).strip()
                )
