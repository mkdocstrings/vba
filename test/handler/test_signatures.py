"""
Test complete VBA signatures and their presentation options.
"""

import re
import unittest
from html import unescape
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocs.commands.build import build
from mkdocs.config import load_config

from mkdocstrings_handlers.vba._util import parse_signature, find_procedures
from test.helpers import assert_no_warnings


class TestSignatures(unittest.TestCase):
    """
    Preserve explicit declarations without adding implicit types to signatures.
    """

    def test_authored_signatures(self) -> None:
        """
        Keep return types, arrays, modifiers, default values, and keyword spelling.
        """
        for declaration in (
            'Public Function choose(Optional ByVal value As String = "hello") As String',
            "Property Get currentValue() As Long",
            "Private Sub consume(ByRef values() As Variant)",
            "Function combine(ParamArray values() As Variant)",
            "Function values() As Long()",
            "Function values(first As Long, second As Long) As Long()",
            "pUbLiC fUnCtIoN choose(value)",
        ):
            with self.subTest(declaration=declaration):
                signature = parse_signature(declaration)
                self.assertEqual(
                    declaration, signature.render(show_arguments=True, line_length=None)
                )

    def test_wrapping(self) -> None:
        """
        Wrap separated signatures at argument boundaries using VBA continuations.
        """
        signature = parse_signature(
            "Public Function choose(first As Long, second As Long) As Long"
        )
        self.assertEqual(
            "Public Function choose( _\n    first As Long, _\n    second As Long) As Long",
            signature.render(show_arguments=True, line_length=40),
        )
        long_return = parse_signature(
            "Public Function choose(value As Long, Optional fallback As Long = 2) As Long"
        )
        wrapped = long_return.render(show_arguments=True, line_length=40)
        self.assertIn(") _\n    As Long", wrapped)
        self.assertTrue(all(len(line) <= 40 for line in wrapped.splitlines()))

    def test_array_return_collection(self) -> None:
        """
        Keep array-return procedures and their complete documentation types.
        """
        procedure = next(
            find_procedures(
                "Function values() As Long()\n    ' Return values.\n    '\n"
                "    ' Returns:\n    '     The values.\nEnd Function\n"
            )
        )
        self.assertEqual("Long()", procedure.signature.return_type)
        assert procedure.docstring is not None
        returns = next(
            section
            for section in procedure.docstring.parsed
            if section.kind.value == "returns"
        )
        self.assertEqual("Long()", str(returns.value[0].annotation))

    def test_rendering_options(self) -> None:
        """
        Render complete inline/separate signatures, and omit them when disabled.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            declaration = "Function choose(first As Long, second As Long) As Long"
            (root / "source.bas").write_text(
                declaration + "\n    ' Choose a value.\nEnd Function\n",
                encoding="utf-8",
            )
            for name, options in (
                ("inline", ""),
                ("separate", "      separate_signature: true\n      line_length: 30\n"),
                (
                    "hidden",
                    "      separate_signature: true\n      show_signature: false\n",
                ),
            ):
                (root / "docs" / f"{name}.md").write_text(
                    "# Reference\n\n::: source.bas\n    handler: vba\n    options:\n"
                    "      show_source: false\n" + options,
                    encoding="utf-8",
                )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Signatures\nuse_directory_urls: false\n", encoding="utf-8"
            )
            with assert_no_warnings():
                build(
                    config=load_config(
                        config_file=str(config_file), plugins=["mkdocstrings"]
                    )
                )
            pages = {
                name: (root / "site" / f"{name}.html").read_text(encoding="utf-8")
                for name in ("inline", "separate", "hidden")
            }
            inline = unescape(re.sub(r"<[^>]+>", "", pages["inline"]))
            self.assertIn(declaration, inline)
            separate = unescape(re.sub(r"<[^>]+>", "", pages["separate"]))
            self.assertIn(
                "Function choose( _\n    first As Long, _\n    second As Long) As Long",
                separate,
            )
            for name in ("separate", "hidden"):
                heading = re.search(
                    r'<h[1-6][^>]*id="choose"[^>]*>(.*?)</h[1-6]>',
                    pages[name],
                    re.DOTALL,
                )
                assert heading is not None
                self.assertEqual(
                    "Function choose",
                    unescape(re.sub(r"<[^>]+>", "", heading[1])).strip(),
                )
            self.assertNotIn(
                "first As Long", unescape(re.sub(r"<[^>]+>", "", pages["hidden"]))
            )
            self.assertNotIn("None", inline)
