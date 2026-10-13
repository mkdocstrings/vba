"""
Test string literals containing argument separators, quotes, and apostrophes.
"""

import unittest

from mkdocstrings_handlers.vba._util import (
    find_procedures,
    is_signature,
    parse_signature,
)


class TestQuotedDefaults(unittest.TestCase):
    """
    Preserve complete quoted defaults without treating their contents as VBA separators.
    """

    def test_quoted_defaults(self) -> None:
        """
        Separate parameters only outside strings and retain doubled quotes and apostrophes.
        """
        for default in ('"A,B"', '"A, ""B"""', '"A,B\'s"', '""', '",,"'):
            declaration = f"Public Function choose(Optional ByVal caption As String = {default}, Optional ByRef raw = Empty) As String"
            with self.subTest(default=default):
                signature = parse_signature(declaration + " ' A trailing comment.")
                self.assertEqual(
                    ["caption", "raw"], [argument.name for argument in signature.args]
                )
                self.assertEqual(default, signature.args[0].default)
                self.assertEqual("Empty", signature.args[1].default)
                self.assertEqual("String", signature.return_type)
                self.assertTrue(is_signature(declaration))

    def test_collection(self) -> None:
        """
        Collect the complete procedure rather than silently dropping a quoted-comma declaration.
        """
        procedure = next(
            find_procedures(
                'Function choose(Optional caption As String = "A,B") As String\n'
                "    ' Choose a caption.\nEnd Function\n"
            )
        )
        self.assertEqual('"A,B"', procedure.signature.args[0].default)
        self.assertEqual("choose", procedure.signature.name)

    def test_unterminated_string(self) -> None:
        """
        Reject incomplete string literals instead of combining unrelated parameters.
        """
        declaration = 'Sub choose(Optional caption As String = "A,B)'
        with self.assertRaisesRegex(RuntimeError, "Unterminated string"):
            parse_signature(declaration)
        self.assertFalse(is_signature(declaration))

    def test_empty_arguments(self) -> None:
        """
        Keep rejecting missing parameters outside quoted strings.
        """
        for arguments in (",value", "value,,other", "value,"):
            declaration = f"Sub choose({arguments})"
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(RuntimeError, "Empty argument"):
                    parse_signature(declaration)
                self.assertFalse(is_signature(declaration))
