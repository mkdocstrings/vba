"""
Test rendering of VBA examples in Google-style documentation comments.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from test.test_examples import tmp_build


class TestDocstringExamples(unittest.TestCase):
    """
    Keep plain VBA examples visible alongside doctest-style examples.
    """

    def test_plain_vba_example(self) -> None:
        """
        Render the example itself when source display cannot mask missing content.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "docs/index.md").write_text(
                "::: numbers.bas\n"
                "    handler: vba\n"
                "    options:\n"
                "      show_source: false\n",
                encoding="utf-8",
            )
            (root / "numbers.bas").write_text(
                "Public Function DoubleValue(value As Double) As Double\n"
                "    ' Double a number.\n"
                "    '\n"
                "    ' Examples:\n"
                "    '     Debug.Print DoubleValue(4)\n"
                "    DoubleValue = value * 2\n"
                "End Function\n",
                encoding="utf-8",
            )
            config = root / "mkdocs.yml"
            config.write_text(
                "site_name: Examples\ntheme: material\nplugins:\n  - mkdocstrings\n",
                encoding="utf-8",
            )
            with tmp_build(config) as site:
                html = (site / "index.html").read_text(encoding="utf-8")
        self.assertIn("Examples:", html)
        self.assertIn("Debug.Print DoubleValue(4)", html)
        self.assertNotIn("End Function", html)
