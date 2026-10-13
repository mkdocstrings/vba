"""
Test physical source locations and displayed VBA source.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from griffe import Function, Module

from mkdocstrings_handlers.vba import get_handler
from mkdocstrings_handlers.vba._util import (
    collapse_long_lines,
    find_file_docstring,
    find_procedures,
)


class TestSourceLocations(unittest.TestCase):
    """
    Preserve physical lines while parsing logical VBA statements.
    """

    def test_continuations_and_warning_locations(self) -> None:
        """
        Locate later warnings after preceding and signature continuations in LF and CRLF.
        """
        lines = [
            "Private Const offset As Long = 1 + _",
            "    2",
            "' Module documentation.",
            "",
            "\tPublic Function choose( _",
            "\t    value As Long, _",
            "\t    Optional fallback As Long = 2) As Long",
            "\t    '",
            "\t    ' Choose a value.",
            "\t    '",
            "\t    ' Args:",
            "\t    '     MISSING (Long): An unknown parameter.",
            "\t    If value Then",
            "\t        choose = value",
            "\t    End If",
            "\tEnd Function ' Finished choosing.",
            "",
            "Public Sub later(value)",
            "    ' Document another procedure.",
            "    '",
            "    ' Args:",
            "    '     UNKNOWN (String): Another unknown parameter.",
            "    value = 1 + _",
            "        2",
            "End Sub",
        ]
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)), TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / "source.bas"
                path.write_bytes(newline.join(lines).encode("utf-8"))
                handler = get_handler(
                    tool_config={"config_file_path": root / "mkdocs.yml"}
                )
                module = handler.collect(identifier="source.bas", config={})
                self.assertEqual(lines, module.source)
                self.assertEqual(2, len(module.procedures))
                first, later = module.procedures
                self.assertEqual((5, 16), (first.first_line, first.last_line))
                self.assertEqual((18, 25), (later.first_line, later.last_line))
                self.assertEqual(lines[4:16], first.source)
                self.assertEqual(lines[17:25], later.source)
                self.assertEqual(
                    ["value", "fallback"], [a.name for a in first.signature.args]
                )
                assert module.docstring is not None
                self.assertEqual(3, module.docstring.lineno)
                self.assertIsInstance(module.docstring.parent, Module)
                assert module.docstring.parent is not None
                self.assertEqual(path, module.docstring.parent.filepath)
                for procedure, start, end, doc_start, warning_line in (
                    (first, 5, 16, 9, 12),
                    (later, 18, 25, 19, 22),
                ):
                    assert procedure.docstring is not None
                    parent = procedure.docstring.parent
                    self.assertIsInstance(parent, Function)
                    assert parent is not None
                    self.assertIs(parent.parent, module.docstring.parent)
                    self.assertEqual(path, parent.filepath)
                    self.assertEqual((start, end), (parent.lineno, parent.endlineno))
                    self.assertEqual(doc_start, procedure.docstring.lineno)
                    with self.assertLogs(level="WARNING") as captured:
                        _ = procedure.docstring.parsed
                    self.assertEqual(1, len(captured.output))
                    self.assertIn(
                        f"{path}:{warning_line}: Parameter", captured.output[0]
                    )

    def test_matching_terminators(self) -> None:
        """
        End only at the matching procedure terminator and include that line in source.
        """
        for kind, terminator in (
            ("Sub", "Sub"),
            ("Function", "Function"),
            ("Property Get", "Property"),
            ("Property Let", "Property"),
        ):
            with self.subTest(kind=kind):
                lines = [
                    f"{kind} first()",
                    "    ' First procedure.",
                    "End If",
                    "End With",
                    "End Select",
                    "EndValue = 1",
                    "End",
                    "End " + ("Sub" if terminator != "Sub" else "Function"),
                    f"  eNd {terminator.upper()} ' Finished.",
                    "Sub second()",
                    "    ' Second procedure.",
                    "End Sub",
                ]
                first, second = find_procedures("\n".join(lines))
                self.assertEqual(lines[:9], first.source)
                self.assertEqual((1, 9), (first.first_line, first.last_line))
                self.assertEqual(lines[9:], second.source)

    def test_comment_underscore(self) -> None:
        """
        Preserve comment underscores without swallowing a following terminator.
        """
        lines = ["Sub first()", "    ' Keep this underscore _", "End Sub"]
        procedure = next(find_procedures("\n".join(lines)))
        self.assertEqual(lines, procedure.source)
        assert procedure.docstring is not None
        self.assertEqual("Keep this underscore _", procedure.docstring.value)

    def test_file_docstring_stops_before_continued_signature(self) -> None:
        """
        Keep procedure comments out of the module documentation.
        """
        code = """
' Module documentation.
Public Function choose( _
    value)
    ' Procedure documentation.
End Function
"""
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                source = code.replace("\n", newline)
                docstring = find_file_docstring(source)
                self.assertEqual("Module documentation.", docstring.value)
                self.assertEqual(2, docstring.lineno)
                procedure = next(find_procedures(source))
                self.assertEqual((3, 6), (procedure.first_line, procedure.last_line))
                self.assertEqual(source.splitlines()[2:6], procedure.source)

    def test_collapse_long_lines_behavior(self) -> None:
        """
        Retain the standalone continuation helper's existing behavior.
        """
        self.assertEqual("hello world", collapse_long_lines("hello _\nworld"))
        self.assertEqual("hello world", collapse_long_lines("hello _  \nworld"))
        self.assertEqual("hello _ world", collapse_long_lines("hello _ world"))
        self.assertEqual("hello \nworld", collapse_long_lines("hello _\r\nworld"))
