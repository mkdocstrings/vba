"""
Test physical source locations and displayed VBA source.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from griffe import Function, Module

from mkdocstrings_handlers.vba import get_handler
from mkdocstrings_handlers.vba._util import (
    _logical_lines,
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

    def test_inline_comment_underscore(self) -> None:
        """
        Keep inline comment underscores from swallowing terminators and later procedures.
        """
        for statement in (
            "    value = 1 ' explanation _",
            "    value = \"don't\" ' explanation _",
            '    value = "say ""it\'s done""" \' explanation _',
        ):
            with self.subTest(statement=statement):
                lines = ["Sub first()", "    ' First.", statement, "End Sub"]
                later = ["Sub later()", "    ' Later.", "End Sub"]
                procedures = list(find_procedures("\n".join(lines + later)))
                self.assertEqual(
                    ["first", "later"], [p.signature.name for p in procedures]
                )
                self.assertEqual(lines, procedures[0].source)
                self.assertEqual(
                    (1, 4), (procedures[0].first_line, procedures[0].last_line)
                )
                self.assertEqual(later, procedures[1].source)
                final_procedure = list(find_procedures("\n".join(lines)))
                self.assertEqual(1, len(final_procedure))
                self.assertEqual(lines, final_procedure[0].source)

    def test_terminator_comment_underscore(self) -> None:
        """
        Keep an underscore in a terminator comment from absorbing the next signature.
        """
        for terminator in ("End Sub ' explanation _", "End Sub: Rem explanation _"):
            with self.subTest(terminator=terminator):
                lines = ["Sub first()", "    ' First.", terminator]
                later = ["Sub later()", "    ' Later.", "End Sub"]
                first, second = find_procedures("\n".join(lines + later))
                self.assertEqual(lines, first.source)
                self.assertEqual((1, 3), (first.first_line, first.last_line))
                self.assertEqual(later, second.source)

    def test_rem_comment_underscore(self) -> None:
        """
        Preserve procedure boundaries around Rem comments, labels, and line numbers.
        """
        for statement in (
            "    Rem explanation _",
            "\trEm explanation _",
            "10 Rem explanation _",
            "label: Rem explanation _",
            "    value = 1: Rem explanation _",
            '    value = "prefix: Rem" : Rem "quoted comment _',
        ):
            for newline in ("\n", "\r\n"):
                with self.subTest(statement=statement, newline=repr(newline)):
                    lines = ["Sub first()", "    ' First.", statement, "End Sub"]
                    later = ["Sub later()", "    ' Later.", "End Sub"]
                    first, second = find_procedures(newline.join(lines + later))
                    self.assertEqual(lines, first.source)
                    self.assertEqual((1, 4), (first.first_line, first.last_line))
                    self.assertEqual(later, second.source)
                    final_procedure = list(find_procedures(newline.join(lines)))
                    self.assertEqual(1, len(final_procedure))
                    self.assertEqual(lines, final_procedure[0].source)
                    assert first.docstring is not None
                    self.assertEqual("First.", first.docstring.value)

    def test_rem_text_in_continuations(self) -> None:
        """
        Keep genuine continuations containing Rem text in identifiers or quoted strings.
        """
        for statement in (
            "remaining = 1 + _",
            'value = "Rem explanation" & _',
            'value = "prefix: Rem explanation" & _',
            'value = "say ""Rem don\'t""" & _',
        ):
            with self.subTest(statement=statement):
                self.assertEqual(
                    [(statement[:-1] + '    " next"', 1, 2)],
                    list(_logical_lines(lines=[statement, '    " next"'])),
                )

    def test_quoted_apostrophes_in_continuations(self) -> None:
        """
        Continue code containing apostrophes and escaped quotes inside string literals.
        """
        for expression in ('"don\'t"', '"say ""it\'s done"""'):
            with self.subTest(expression=expression):
                lines = [f"value = {expression} & _", '    " next"']
                self.assertEqual(
                    [(f'value = {expression} &     " next"', 1, 2)],
                    list(_logical_lines(lines=lines)),
                )

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
