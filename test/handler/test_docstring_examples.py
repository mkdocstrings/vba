"""
Test prose, fenced VBA code, and interactive examples in documentation.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocs.commands.build import build
from mkdocs.config import load_config

from test.helpers import assert_no_warnings


class TestDocstringExamples(unittest.TestCase):
    """
    Render every example subsection supplied by supported Griffe versions.
    """

    def test_mixed_examples(self) -> None:
        """
        Keep prose, fenced code, explicit links, and interactive examples in order.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "source.bas").write_text(
                "Public Sub example()\n    ' Demonstrate examples.\n    '\n"
                "    ' Examples:\n"
                "    '     Start with **bold prose** and [a link](https://example.com).\n"
                "    '\n    '     ```vb\n    '     MsgBox \"fenced example\"\n"
                "    '     ```\n    '\n"
                "    '     >>> example()\n    '     interactive result\n    '\n"
                "    '     Finish with trailing prose.\nEnd Sub\n",
                encoding="utf-8",
            )
            (root / "docs/index.md").write_text(
                "# Reference\n\n::: source.bas\n    handler: vba\n"
                "    options:\n      show_source: false\n",
                encoding="utf-8",
            )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Examples\nmarkdown_extensions:\n  - fenced_code\n",
                encoding="utf-8",
            )
            with assert_no_warnings():
                config = load_config(
                    config_file=str(config_file), plugins=["mkdocstrings"]
                )
                build(config=config)
            html = (root / "site/index.html").read_text(encoding="utf-8")
            self.assertIn("<strong>bold prose</strong>", html)
            self.assertIn('href="https://example.com"', html)
            self.assertIn('class="language-vb"', html)
            self.assertIn("fenced example", html)
            self.assertIn("interactive result", html)
            self.assertIn("Finish with trailing prose.", html)
            self.assertLess(html.index("bold prose"), html.index("fenced example"))
            self.assertLess(
                html.index("fenced example"), html.index("interactive result")
            )
            self.assertLess(
                html.index("interactive result"), html.index("trailing prose")
            )
            self.assertNotIn("<summary>Source code</summary>", html)
