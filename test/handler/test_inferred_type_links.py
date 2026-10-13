"""
Test links for types inferred from VBA signatures without linking default values.
"""

import unittest

from griffe import ExprName
from mkdocs_autorefs import fix_refs

from mkdocstrings_handlers.vba import get_handler
from mkdocstrings_handlers.vba._crossref import do_vba_annotation
from mkdocstrings_handlers.vba._util import find_procedures


class TestInferredTypeLinks(unittest.TestCase):
    """
    Link custom signature types while retaining built-in and literal values.
    """

    def test_inferred_annotations(self) -> None:
        """
        Infer a referenceable custom parameter and return type from the signature.
        """
        procedure = next(
            find_procedures(
                "Function make(value As Widget) As Widget\n    ' Make a widget.\n"
                "    '\n    ' Args:\n    '     value: The input widget.\n"
                "    '\n    ' Returns:\n    '     The resulting widget.\nEnd Function\n"
            )
        )
        assert procedure.docstring is not None
        handler = get_handler()
        handler.update_env({})
        for section in procedure.docstring.parsed:
            if section.kind.value in ("parameters", "returns"):
                annotation = section.value[0].annotation
                html = handler.env.get_template("expression.html").render(
                    expression=do_vba_annotation(annotation)
                )
                self.assertIn('<autoref identifier="Widget" optional>', html)

    def test_builtins_and_parsed_annotations(self) -> None:
        """
        Keep implicit Variant, built-ins, and explicit Griffe annotations unchanged.
        """
        for name in ("Variant", "String", "Long", "LongPtr", "bOoLeAn"):
            self.assertEqual(name, do_vba_annotation(name))
        annotation = ExprName(name="Widget", parent=None)
        self.assertIs(annotation, do_vba_annotation(annotation))

    def test_optional_qualified_reference(self) -> None:
        """
        Retain full qualified identifiers, resolving available targets and hovering missing ones.
        """
        handler = get_handler()
        handler.update_env({})
        html = handler.env.get_template("expression.html").render(
            expression=do_vba_annotation("Library.Widget")
        )
        resolved, missing = fix_refs(
            html, lambda identifier: ("widget.html#Widget", None)
        )
        self.assertFalse(missing)
        self.assertIn('href="widget.html#Widget"', resolved)
        self.assertIn("Library.Widget", resolved)

    def test_default_values_remain_literals(self) -> None:
        """
        Keep names and quoted strings in defaults out of automatic type linking.
        """
        handler = get_handler()
        handler.update_env({})
        for default in ("Widget", '"Widget"', "Nothing"):
            html = handler.env.get_template("expression.html").render(
                expression=default
            )
            self.assertNotIn("autoref", html)
