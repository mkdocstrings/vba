"""
Test VBA parameter matching during Google-style docstring parsing.
"""

import unittest

from griffe import (
    DocstringParameter,
    DocstringSectionParameters,
    Function,
    Parameter,
    Parameters,
)

from mkdocstrings_handlers.vba._types import VbaProcedureInfo
from mkdocstrings_handlers.vba._util import find_procedures
from test.helpers import assert_no_warnings


def _parse_parameters(
    *, code: str
) -> tuple[VbaProcedureInfo, list[DocstringParameter]]:
    """
    Collect a procedure and parse its parameter documentation.

    Args:
        code: VBA source containing one procedure with an Args section.

    Returns:
        The procedure and its parsed parameter documentation.
    """
    procedure = next(find_procedures(code))
    assert procedure.docstring is not None
    section = next(
        section
        for section in procedure.docstring.parsed
        if isinstance(section, DocstringSectionParameters)
    )
    return procedure, section.value


class TestParameterDocstrings(unittest.TestCase):
    """
    Match VBA names independently of casing while preserving authored text.
    """

    def test_mixed_case_names(self) -> None:
        """
        Find annotations and defaults without changing signature or docstring spelling.
        """
        with assert_no_warnings():
            procedure, parameters = _parse_parameters(
                code="""Function choose(camelCase As String, Optional count As Long = 2) As String
    ' Choose a value.
    '
    ' Args:
    '     CAMELCASE: The value.
    '     COUNT: The number of values.
End Function"""
            )
        self.assertEqual(["CAMELCASE", "COUNT"], [p.name for p in parameters])
        self.assertEqual(["String", "Long"], [p.annotation for p in parameters])
        self.assertEqual("2", parameters[1].value)
        self.assertEqual(
            ["camelCase", "count"], [a.name for a in procedure.signature.args]
        )
        self.assertEqual(
            "Optional count As Long = 2", procedure.signature.args[1].render()
        )
        assert procedure.docstring is not None
        self.assertIn("CAMELCASE: The value.", procedure.docstring.value)

    def test_explicit_annotation(self) -> None:
        """
        Preserve an explicit docstring type while retrieving a differently cased default.
        """
        with assert_no_warnings():
            _, parameters = _parse_parameters(
                code="""Sub useWidget(Optional value As String = "sample")
    ' Use a widget.
    '
    ' Args:
    '     VALUE (Widget): The value.
End Sub"""
            )
        self.assertEqual("VALUE", parameters[0].name)
        self.assertEqual("Widget", str(parameters[0].annotation))
        self.assertEqual('"sample"', parameters[0].value)

    def test_unknown_parameter_warning(self) -> None:
        """
        Keep warnings for parameter names absent from the signature.
        """
        with self.assertLogs(level="WARNING") as captured:
            _, parameters = _parse_parameters(code="""Sub useValue(value As String)
    ' Use a value.
    '
    ' Args:
    '     MISSING (String): An incorrect parameter.
End Sub""")
        self.assertEqual(1, len(captured.output))
        self.assertIn(
            "Parameter 'MISSING' does not appear in the function signature",
            captured.output[0],
        )
        self.assertEqual("MISSING", parameters[0].name)

    def test_lookup_and_membership(self) -> None:
        """
        Preserve indexed access and parameter identity while matching names by case.
        """
        with assert_no_warnings():
            procedure, _ = _parse_parameters(code="""Sub useValue(camelCase As String)
    ' Use a value.
    '
    ' Args:
    '     CAMELCASE: The value.
End Sub""")
        assert procedure.docstring is not None
        assert isinstance(procedure.docstring.parent, Function)
        parameters = procedure.docstring.parent.parameters
        self.assertIs(parameters[0], parameters["CAMELCASE"])
        self.assertIs(parameters[-1], parameters["camelcase"])
        self.assertIn("CAMELCASE", parameters)
        self.assertNotIn("missing", parameters)
        with self.assertRaises(KeyError):
            parameters["missing"]
        with self.assertRaises(IndexError):
            parameters[1]

    def test_param_array(self) -> None:
        """
        Match a differently cased ParamArray name and preserve Griffe's starred lookup.
        """
        with assert_no_warnings():
            procedure, parsed = _parse_parameters(
                code="""Sub useValues(ParamArray Args() As Variant)
    ' Use the values.
    '
    ' Args:
    '     args: The values.
End Sub"""
            )
        self.assertEqual("args", parsed[0].name)
        self.assertEqual("Variant", parsed[0].annotation)
        assert procedure.docstring is not None
        assert isinstance(procedure.docstring.parent, Function)
        parameters = procedure.docstring.parent.parameters
        self.assertIs(parameters[0], parameters["*aRgS"])
        self.assertIs(parameters[0], parameters["**ARGS"])
        self.assertIn("*ARGS", parameters)
        self.assertEqual("Args", procedure.signature.args[0].name)

    def test_other_griffe_parameters(self) -> None:
        """
        Leave ordinary Griffe parameter containers case-sensitive.
        """
        parameters = Parameters(Parameter(name="camelCase", annotation="str"))
        self.assertNotIn("CAMELCASE", parameters)
        with self.assertRaises(KeyError):
            parameters["CAMELCASE"]
