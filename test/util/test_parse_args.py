import unittest

# noinspection PyProtectedMember
from mkdocstrings_handlers.vba._types import VbaArgumentInfo

# noinspection PyProtectedMember
from mkdocstrings_handlers.vba._util import parse_args, parse_arg


class TestParseArg(unittest.TestCase):
    def test_1(self) -> None:
        cases = [
            (
                "bar As listObject",
                VbaArgumentInfo(
                    name="bar",
                    optional=False,
                    modifier=None,
                    arg_type="listObject",
                    default=None,
                ),
            ),
            (
                "ByVal v As Variant",
                VbaArgumentInfo(
                    name="v",
                    optional=False,
                    modifier="ByVal",
                    arg_type="Variant",
                    default=None,
                ),
            ),
            (
                'Optional ByRef s1 As String = "Hello"',
                VbaArgumentInfo(
                    name="s1",
                    optional=True,
                    modifier="ByRef",
                    arg_type="String",
                    default='"Hello"',
                ),
            ),
            (
                "ParamArray Args() As Variant",
                VbaArgumentInfo(
                    name="Args",
                    optional=False,
                    modifier="ParamArray",
                    arg_type="Variant",
                    default=None,
                ),
            ),
        ]

        for arg_string, result in cases:
            with self.subTest(arg_string):
                self.assertEqual(result, parse_arg(arg_string))


class TestParseArgs(unittest.TestCase):
    def test_1(self) -> None:
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
        ]

        for args_string, result in cases:
            with self.subTest(args_string):
                self.assertEqual(result, list(parse_args(args_string)))


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )
