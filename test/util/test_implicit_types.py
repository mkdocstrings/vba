"""
Test implicit VBA types during Google-style docstring parsing.
"""

import unittest

from griffe import (
    DocstringSection,
    DocstringSectionParameters,
    DocstringSectionReturns,
    Function,
)

from mkdocstrings_handlers.vba._types import VbaProcedureInfo
from mkdocstrings_handlers.vba._util import find_procedures
from test.helpers import assert_no_warnings


def _parse_docstring(*, code: str) -> tuple[VbaProcedureInfo, list[DocstringSection]]:
    """
    Collect a procedure and parse its documentation.

    Args:
        code: VBA source containing one documented procedure.

    Returns:
        The procedure and its parsed documentation sections.
    """
    procedure = next(find_procedures(code))
    assert procedure.docstring is not None
    return procedure, procedure.docstring.parsed


class TestImplicitTypes(unittest.TestCase):
    """
    Infer Variant for documentation while retaining authored signatures.
    """

    def test_untyped_parameters(self) -> None:
        """
        Infer untyped arguments, including optional defaults and mixed-case names.
        """
        with assert_no_warnings():
            procedure, sections = _parse_docstring(code="""
Sub useValues(value, Optional fallback = 2, ParamArray items())
    ' Use the supplied values.
    '
    ' Args:
    '     VALUE: The input value.
    '     fallback: The fallback value.
    '     items: Additional values.
End Sub
""")
        parameters = next(
            s.value for s in sections if isinstance(s, DocstringSectionParameters)
        )
        self.assertEqual(["Variant"] * 3, [p.annotation for p in parameters])
        self.assertEqual("2", parameters[1].value)
        self.assertEqual([None] * 3, [a.arg_type for a in procedure.signature.args])
        self.assertEqual("value", procedure.signature.args[0].render())
        self.assertEqual("Optional fallback = 2", procedure.signature.args[1].render())
        self.assertEqual("ParamArray items", procedure.signature.args[2].render())
        self.assertNotIn("As Variant", "\n".join(procedure.source))

    def test_untyped_returns(self) -> None:
        """
        Infer Function and Property Get returns regardless of keyword casing.
        """
        for kind, terminator in (
            ("fUnCtIoN", "Function"),
            ("pRoPeRtY gEt", "Property"),
        ):
            with self.subTest(kind=kind), assert_no_warnings():
                procedure, sections = _parse_docstring(code=f"""
{kind} getValue()
    ' Get the value.
    '
    ' Returns:
    '     The selected value.
End {terminator}
""")
                returns = next(
                    s.value for s in sections if isinstance(s, DocstringSectionReturns)
                )
                self.assertEqual("Variant", returns[0].annotation)
                self.assertIsNone(procedure.signature.return_type)
                self.assertEqual(kind, procedure.signature.procedure_type)
                self.assertNotIn("As Variant", "\n".join(procedure.source))

    def test_explicit_signature_types(self) -> None:
        """
        Retain explicit parameter and return types beside implicit ones.
        """
        with assert_no_warnings():
            procedure, sections = _parse_docstring(code="""
Function getValue(value As Long, fallback) As String
    ' Get a string value.
    '
    ' Args:
    '     value: The input value.
    '     fallback: The fallback value.
    '
    ' Returns:
    '     The selected value.
End Function
""")
        parameters = next(
            s.value for s in sections if isinstance(s, DocstringSectionParameters)
        )
        returns = next(
            s.value for s in sections if isinstance(s, DocstringSectionReturns)
        )
        self.assertEqual(["Long", "Variant"], [p.annotation for p in parameters])
        self.assertEqual("String", returns[0].annotation)
        self.assertEqual("Long", procedure.signature.args[0].arg_type)
        self.assertEqual("String", procedure.signature.return_type)

    def test_explicit_docstring_types(self) -> None:
        """
        Give explicit documentation types precedence over implicit Variant metadata.
        """
        with assert_no_warnings():
            _, sections = _parse_docstring(code="""
Function getValue(Optional value = 2)
    ' Get a string value.
    '
    ' Args:
    '     VALUE (Long): The input value.
    '
    ' Returns:
    '     result (String): The selected value.
End Function
""")
        parameters = next(
            s.value for s in sections if isinstance(s, DocstringSectionParameters)
        )
        returns = next(
            s.value for s in sections if isinstance(s, DocstringSectionReturns)
        )
        self.assertEqual("Long", str(parameters[0].annotation))
        self.assertEqual("2", parameters[0].value)
        self.assertEqual("String", str(returns[0].annotation))

    def test_procedures_without_returns(self) -> None:
        """
        Infer argument types for Sub and Property Let without giving them returns.
        """
        for kind, terminator in (("Sub", "Sub"), ("Property Let", "Property")):
            with self.subTest(kind=kind), assert_no_warnings():
                procedure, sections = _parse_docstring(code=f"""
{kind} setValue(value)
    ' Set the value.
    '
    ' Args:
    '     value: The new value.
End {terminator}
""")
                assert procedure.docstring is not None
                assert isinstance(procedure.docstring.parent, Function)
                self.assertIsNone(procedure.docstring.parent.returns)
                parameters = next(
                    s.value
                    for s in sections
                    if isinstance(s, DocstringSectionParameters)
                )
                self.assertEqual("Variant", parameters[0].annotation)

    def test_invalid_return_documentation(self) -> None:
        """
        Keep missing-return-type warnings for Sub and Property Let documentation.
        """
        for kind, terminator in (("Sub", "Sub"), ("Property Let", "Property")):
            with self.subTest(kind=kind), self.assertLogs(level="WARNING") as captured:
                _parse_docstring(code=f"""
{kind} setValue(value)
    ' Set the value.
    '
    ' Returns:
    '     The selected value.
End {terminator}
""")
            self.assertEqual(1, len(captured.output))
            self.assertIn(
                "No type or annotation for returned value", captured.output[0]
            )

    def test_unknown_parameter_warning(self) -> None:
        """
        Keep warnings for unknown names even when declared arguments are untyped.
        """
        with self.assertLogs(level="WARNING") as captured:
            _parse_docstring(code="""
Sub useValue(value)
    ' Use the supplied value.
    '
    ' Args:
    '     MISSING (String): An incorrect parameter.
End Sub
""")
        self.assertEqual(1, len(captured.output))
        self.assertIn(
            "Parameter 'MISSING' does not appear in the function signature",
            captured.output[0],
        )
