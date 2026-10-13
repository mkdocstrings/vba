"""
Test VBA object setters and unique, stable property accessor anchors.
"""

import unittest
from pathlib import Path

from griffe import Function
from mkdocstrings_handlers.vba._types import VbaModuleInfo
from mkdocstrings_handlers.vba._util import find_procedures, parse_signature
from test.helpers import assert_no_warnings


class TestPropertyAccessors(unittest.TestCase):
    """
    Collect Set accessors and retain a canonical anchor for each property.
    """

    def test_property_set(self) -> None:
        """
        Parse object setters and infer argument types without assigning a return type.
        """
        declaration = (
            "Public Property Set Item(ByVal key As String, ByVal value As Object)"
        )
        self.assertEqual("Property Set", parse_signature(declaration).procedure_type)
        with assert_no_warnings():
            procedure = next(
                find_procedures(
                    declaration + "\n    ' Set the item.\n    '\n"
                    "    ' Args:\n    '     KEY: The key.\n    '     VALUE: The object.\nEnd Property\n"
                )
            )
            assert procedure.docstring is not None
            assert isinstance(procedure.docstring.parent, Function)
            self.assertIsNone(procedure.docstring.parent.returns)
            self.assertEqual(
                ["String", "Object"],
                [
                    str(p.annotation)
                    for section in procedure.docstring.parsed
                    if section.kind.value == "parameters"
                    for p in section.value
                ],
            )

    def test_anchors(self) -> None:
        """
        Keep getter/standalone anchors and suffix companion accessors regardless of source order.
        """
        procedures = list(
            find_procedures(
                "Property Set Item(value)\n    ' Set an object.\nEnd Property\n"
                "Property Get Item()\n    ' Get an item.\nEnd Property\n"
                "Property Let Item(value)\n    ' Set a value.\nEnd Property\n"
            )
        )
        module = VbaModuleInfo(
            docstring=None, source=[], path=Path("Item.cls"), procedures=procedures
        )
        self.assertEqual(
            ["Item--set", "Item", "Item--let"],
            [
                module.procedure_anchor(procedure=p, show_if_no_docstring=False)
                for p in procedures
            ],
        )
        module.procedures = procedures[:1]
        self.assertEqual(
            "Item",
            module.procedure_anchor(
                procedure=procedures[0], show_if_no_docstring=False
            ),
        )

        module.procedures = [procedures[0], procedures[2]]
        self.assertEqual(
            ["Item", "Item--let"],
            [
                module.procedure_anchor(procedure=p, show_if_no_docstring=False)
                for p in module.procedures
            ],
        )

    def test_distinct_authored_casing(self) -> None:
        """
        Preserve existing differently cased IDs that do not collide in HTML.
        """
        procedures = list(
            find_procedures(
                "Property Get Item()\n    ' Get an item.\nEnd Property\n"
                "Property Set item(value)\n    ' Set an item.\nEnd Property\n"
            )
        )
        module = VbaModuleInfo(
            docstring=None, source=[], path=Path("Item.cls"), procedures=procedures
        )
        self.assertEqual(
            ["Item", "item"],
            [
                module.procedure_anchor(procedure=p, show_if_no_docstring=False)
                for p in procedures
            ],
        )

    def test_hidden_getter(self) -> None:
        """
        Keep a bare anchor when only a setter has visible documentation.
        """
        procedures = list(
            find_procedures(
                "Property Get Item()\nEnd Property\n"
                "Property Set Item(value)\n    ' Set an object.\nEnd Property\n"
            )
        )
        procedures[0].docstring = None
        module = VbaModuleInfo(
            docstring=None, source=[], path=Path("Item.cls"), procedures=procedures
        )
        self.assertEqual(
            "Item",
            module.procedure_anchor(
                procedure=procedures[1], show_if_no_docstring=False
            ),
        )
        self.assertEqual(
            "Item--set",
            module.procedure_anchor(procedure=procedures[1], show_if_no_docstring=True),
        )
