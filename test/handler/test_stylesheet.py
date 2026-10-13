"""
Test automatic VBA stylesheet delivery and template overrides.
"""

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mkdocstrings_handlers.vba import get_handler
from mkdocstrings_handlers.vba._types import VbaModuleInfo


class TestStylesheet(unittest.TestCase):
    """
    Include the bundled stylesheet for the native Zensical Markdown integration.
    """

    def test_native_rendering(self) -> None:
        """
        Deliver the full handler stylesheet without requiring a builder plugin.
        """
        handler = get_handler(mdx=["zensical.extensions.mkdocstrings"])
        handler.update_env({})
        module = VbaModuleInfo(
            docstring=None, source=[], path=Path("empty.bas"), procedures=[]
        )
        html = handler.render(module, handler.get_options({}))
        styles = re.findall(
            r"<style data-mkdocstrings-vba>(.*?)</style>", html, re.DOTALL
        )
        self.assertEqual(1, len(styles))
        self.assertTrue(handler.extra_css.strip())
        self.assertEqual(handler.extra_css.strip(), styles[0].strip())

    def test_mkdocs_rendering(self) -> None:
        """
        Keep MkDocs stylesheet delivery through its existing external asset.
        """
        handler = get_handler()
        handler.update_env({})
        module = VbaModuleInfo(
            docstring=None, source=[], path=Path("empty.bas"), procedures=[]
        )
        html = handler.render(module, handler.get_options({}))
        self.assertNotIn("<style", html)
        self.assertIn(".doc-contents td code", handler.extra_css)

    def test_template_override(self) -> None:
        """
        Allow custom module templates to replace the stylesheet block.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "vba" / "material" / "module.html"
            template.parent.mkdir(parents=True)
            template.write_text(
                '{% extends "_base/module.html" %}'
                "{% block stylesheet %}<style>.custom { color: red; }</style>{% endblock %}",
                encoding="utf-8",
            )
            handler = get_handler(
                mdx=["zensical.extensions.mkdocstrings"], custom_templates=str(root)
            )
            handler.update_env({})
            module = VbaModuleInfo(
                docstring=None, source=[], path=Path("empty.bas"), procedures=[]
            )
            html = handler.render(module, handler.get_options({}))
        self.assertIn("<style>.custom { color: red; }</style>", html)
        self.assertNotIn("data-mkdocstrings-vba", html)
