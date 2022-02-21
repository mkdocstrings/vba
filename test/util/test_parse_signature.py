import unittest

from mkdocstrings_handlers.vba.types import VbaSignatureInfo, VbaArgumentInfo
from mkdocstrings_handlers.vba.util import parse_signature


class TestParseSignature(unittest.TestCase):
    def test_1(self):
        cases = [
            (
                "Sub foo()",
                VbaSignatureInfo(
                    visibility=None,
                    return_type=None,
                    procedure_type="Sub",
                    name="foo",
                    args=[],
                ),
            ),
            (
                "Function asdf123(fooBar As listObject)",
                VbaSignatureInfo(
                    visibility=None,
                    return_type=None,
                    procedure_type="Function",
                    name="asdf123",
                    args=[
                        VbaArgumentInfo(
                            name="fooBar",
                            optional=False,
                            modifier=None,
                            arg_type="listObject",
                            default=None,
                        )
                    ],
                ),
            ),
            (
                "Public Property Let asdf(ByVal vNewValue As Variant)",
                VbaSignatureInfo(
                    visibility="Public",
                    return_type=None,
                    procedure_type="Property Let",
                    name="asdf",
                    args=[
                        VbaArgumentInfo(
                            name="vNewValue",
                            optional=False,
                            modifier="ByVal",
                            arg_type="Variant",
                            default=None,
                        )
                    ],
                ),
            ),
            (
                "Function Test(Optional d As Variant = Empty)",
                VbaSignatureInfo(
                    visibility=None,
                    return_type=None,
                    procedure_type="Function",
                    name="Test",
                    args=[
                        VbaArgumentInfo(
                            name="d",
                            optional=True,
                            modifier=None,
                            arg_type="Variant",
                            default="Empty",
                        )
                    ],
                ),
            ),
            (
                "Function dict(ParamArray Args() As Variant)",
                VbaSignatureInfo(
                    visibility=None,
                    return_type=None,
                    procedure_type="Function",
                    name="dict",
                    args=[
                        VbaArgumentInfo(
                            name="Args",
                            optional=False,
                            modifier="ParamArray",
                            arg_type="Variant",
                            default=None,
                        )
                    ],
                ),
            ),
        ]

        for (signature, result) in cases:
            with self.subTest(signature):
                self.assertEqual(result, parse_signature(signature))


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )
