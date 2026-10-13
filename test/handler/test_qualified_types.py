"""
Test qualified VBA types in declarations and generated documentation.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocs.commands.build import build
from mkdocs.config import load_config

from mkdocstrings_handlers.vba._util import (
    find_procedures,
    is_signature,
    parse_arg,
    parse_signature,
)
from test.helpers import assert_no_warnings


class TestQualifiedTypes(unittest.TestCase):
    """
    Preserve dot-separated type identifiers without expanding unrelated syntax.
    """

    def test_parameters(self) -> None:
        """
        Accept qualified types with modifiers, optional defaults, and authored casing.
        """
        for declaration in (
            "value As Excel.Range",
            "ByVal value As Excel.Range",
            "ByRef value As excel.range",
            "Optional ByVal value As Library.Types.Item = Nothing",
        ):
            with self.subTest(declaration=declaration):
                argument = parse_arg(declaration)
                self.assertEqual(declaration, argument.render())

    def test_returns_and_collection(self) -> None:
        """
        Collect functions and property getters with qualified parameter and return types.
        """
        for kind, end in (("Function", "Function"), ("Property Get", "Property")):
            with self.subTest(kind=kind), assert_no_warnings():
                signature = (
                    f"Public {kind} selected(value As Excel.Range) As Excel.Range"
                )
                self.assertTrue(is_signature(signature))
                self.assertEqual("Excel.Range", parse_signature(signature).return_type)
                procedure = next(
                    find_procedures(
                        signature + "\n    ' Return a range.\n    '\n"
                        "    ' Args:\n    '     value: The input range.\n    '\n"
                        "    ' Returns:\n    '     The selected range.\n"
                        + f"End {end}\n"
                    )
                )
                self.assertEqual("Excel.Range", procedure.signature.args[0].arg_type)
                self.assertEqual("Excel.Range", procedure.signature.return_type)
                assert procedure.docstring is not None
                for section in procedure.docstring.parsed:
                    if section.kind.value in ("parameters", "returns"):
                        self.assertEqual(
                            "Excel.Range", str(section.value[0].annotation)
                        )

    def test_malformed_names(self) -> None:
        """
        Reject missing segments and invalid identifier starts in qualified names.
        """
        for name in ("Excel.", "Excel..Range", ".Range", "Excel.1Range"):
            with self.subTest(name=name):
                with self.assertRaises(RuntimeError):
                    parse_arg(f"ByVal value As {name}")
                for signature in (
                    f"Function selected() As {name}",
                    f"Sub consume(value As {name})",
                ):
                    self.assertFalse(is_signature(signature))
                    with self.assertRaises(RuntimeError):
                        parse_signature(signature)

    def test_rendering(self) -> None:
        """
        Keep complete type names and existing procedure anchors in a built site.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "source.bas").write_text(
                "Public Function selected(ByVal value As Excel.Range) As Excel.Range\n"
                "    ' Return the selected range.\n    '\n"
                "    ' Args:\n    '     value: The input range.\n    '\n"
                "    ' Returns:\n    '     The selected range.\nEnd Function\n"
                "Public Sub consume(ByVal value As Excel.Range)\n"
                "    ' Consume a range.\nEnd Sub\n",
                encoding="utf-8",
            )
            (root / "docs/index.md").write_text(
                "# Reference\n\n::: source.bas\n    handler: vba\n", encoding="utf-8"
            )
            config_file = root / "mkdocs.yml"
            config_file.write_text("site_name: Qualified types\n", encoding="utf-8")
            with assert_no_warnings():
                config = load_config(
                    config_file=str(config_file), plugins=["mkdocstrings"]
                )
                build(config=config)
            html = (root / "site/index.html").read_text(encoding="utf-8")
            self.assertIn('id="selected"', html)
            self.assertIn('id="consume"', html)
            self.assertGreaterEqual(html.count("Excel.Range"), 2)
            self.assertIn("The input range.", html)
