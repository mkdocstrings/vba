import unittest

from mkdocstrings_handlers.vba.types import VbaArgumentInfo
from mkdocstrings_handlers.vba.util import parse_args


class TestParseArgs(unittest.TestCase):
    def test_1(self):
        cases = [
            ("", []),
            (
                "foo",
                [
                    VbaArgumentInfo(
                        name="foo",
                        optional=False,
                        modifier=None,
                        arg_type=None,
                        default=None,
                    )
                ],
            ),
            (
                "a,b,c",
                [
                    VbaArgumentInfo(
                        name="a",
                        optional=False,
                        modifier=None,
                        arg_type=None,
                        default=None,
                    ),
                    VbaArgumentInfo(
                        name="b",
                        optional=False,
                        modifier=None,
                        arg_type=None,
                        default=None,
                    ),
                    VbaArgumentInfo(
                        name="c",
                        optional=False,
                        modifier=None,
                        arg_type=None,
                        default=None,
                    ),
                ],
            ),
            (
                "bar As listObject",
                [
                    VbaArgumentInfo(
                        name="bar",
                        optional=False,
                        modifier=None,
                        arg_type="listObject",
                        default=None,
                    )
                ],
            ),
            (
                "ByVal v As Variant",
                [
                    VbaArgumentInfo(
                        name="v",
                        optional=False,
                        modifier="ByVal",
                        arg_type="Variant",
                        default=None,
                    )
                ],
            ),
            (
                'Optional ByRef s1 As String = "Hello"',
                [
                    VbaArgumentInfo(
                        name="s1",
                        optional=True,
                        modifier="ByRef",
                        arg_type="String",
                        default='"Hello"',
                    )
                ],
            ),
        ]

        for (args_string, result) in cases:
            with self.subTest(args_string):
                self.assertEqual(result, list(parse_args(args_string)))


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )