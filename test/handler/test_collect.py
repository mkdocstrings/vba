import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocstrings_handlers.vba import get_handler

# noinspection PyProtectedMember
from mkdocstrings_handlers.vba._types import VbaModuleInfo


def _test_collect(*, write_bytes: bytes, read_encoding: str) -> VbaModuleInfo:
    with TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        handler = get_handler(encoding=read_encoding)
        p = tmp_dir / "source.bas"
        p.write_bytes(write_bytes)
        return handler.collect(identifier=p.as_posix(), config={})


class TestCollect(unittest.TestCase):

    def test_undefined_unicode(self) -> None:
        # See https://symbl.cc/en/unicode-table/#undefined-0 for values that are undefined in Unicode.
        # \xe2\xbf\xaf is utf-8 for the undefined Unicode point U+2FEF
        module_info = _test_collect(
            write_bytes=b"Foo \xe2\xbf\xaf Bar",
            read_encoding="utf-8",
        )
        self.assertEqual(["Foo \u2fef Bar"], module_info.source)

    def test_invalid_utf8(self) -> None:
        # invalid start byte
        module_info = _test_collect(
            write_bytes=b"\x89\x89\x89\x89",
            read_encoding="utf-8",
        )
        self.assertEqual(["����"], module_info.source)

    def test_invalid_latin1(self) -> None:
        module_info = _test_collect(
            write_bytes="🎵".encode("utf-8"),
            read_encoding="latin1",
        )
        # Since `latin1` is a single-byte encoding, it can't detect invalid sequences, and so we get mojibake.
        self.assertEqual(["ð\x9f\x8eµ"], module_info.source)
