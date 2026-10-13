"""
Test documented member ordering and inclusion of undocumented procedures.
"""

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocs.commands.build import build
from mkdocs.config import load_config

from test.helpers import assert_no_warnings


class TestMemberOrderingFiltering(unittest.TestCase):
    """
    Honor the existing ordering and undocumented-member display options.
    """

    def test_empty_module_documentation(self) -> None:
        """
        Omit modules with absent/whitespace docs unless undocumented output is requested.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            for filename, content in (
                ("absent.bas", "Option Explicit\n"),
                ("blank.bas", "'   \n'\t\n"),
            ):
                (root / filename).write_text(content, encoding="utf-8")
                for mode in ("default", "all"):
                    (root / "docs" / f"{filename}-{mode}.md").write_text(
                        f"# Reference\n\n::: {filename}\n    handler: vba\n"
                        "    options:\n      show_root_heading: true\n"
                        f"      show_if_no_docstring: {str(mode == 'all').lower()}\n",
                        encoding="utf-8",
                    )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Empty modules\nuse_directory_urls: false\n",
                encoding="utf-8",
            )
            with assert_no_warnings():
                build(
                    config=load_config(
                        config_file=str(config_file), plugins=["mkdocstrings"]
                    )
                )
            for filename in ("absent.bas", "blank.bas"):
                anchor = f'id="{(root / filename).as_posix()}"'
                default = (root / "site" / f"{filename}-default.html").read_text(
                    encoding="utf-8"
                )
                included = (root / "site" / f"{filename}-all.html").read_text(
                    encoding="utf-8"
                )
                self.assertNotIn(anchor, default)
                self.assertIn(anchor, included)

    def test_ordering_and_filtering(self) -> None:
        """
        Apply case-insensitive alphabetical/source order and retain explicit opt-in to empty docs.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "source.bas").write_text(
                "Sub zebra()\n    ' Zebra documentation.\nEnd Sub\n"
                "Sub Alpha()\n    ' Alpha documentation.\nEnd Sub\n"
                "Sub hidden()\nEnd Sub\n"
                "Sub blank()\n    '   \nEnd Sub\n",
                encoding="utf-8",
            )
            for name, options in (
                ("default", ""),
                ("source", "      members_order: source\n"),
                ("all", "      show_if_no_docstring: true\n"),
            ):
                (root / "docs" / f"{name}.md").write_text(
                    "# Reference\n\n::: source.bas\n    handler: vba\n    options:\n"
                    + options
                    + "      show_source: false\n",
                    encoding="utf-8",
                )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Members\nuse_directory_urls: false\n", encoding="utf-8"
            )
            with assert_no_warnings():
                build(
                    config=load_config(
                        config_file=str(config_file), plugins=["mkdocstrings"]
                    )
                )
            orders = {}
            for name in ("default", "source", "all"):
                html = (root / "site" / f"{name}.html").read_text(encoding="utf-8")
                orders[name] = re.findall(
                    r'<h[1-6]\b[^>]*id="(zebra|Alpha|hidden|blank)"', html
                )
            self.assertEqual(["Alpha", "zebra"], orders["default"])
            self.assertEqual(["zebra", "Alpha"], orders["source"])
            self.assertEqual(["Alpha", "blank", "hidden", "zebra"], orders["all"])
