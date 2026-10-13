"""
Test reference markup and Griffe expression rendering.
"""

from __future__ import annotations

import unittest
from html import unescape

from griffe import ExprName, ExprSubscript
from mkdocs_autorefs import fix_refs

from mkdocstrings_handlers.vba import get_handler
from mkdocstrings_handlers.vba._crossref import do_crossref, do_multi_crossref


def _target_url(identifier: str) -> tuple[str, str | None]:
    """
    Resolve the documented type used in reference tests.

    Args:
        identifier: Reference target to resolve.

    Returns:
        The type documentation URL and title.

    Raises:
        KeyError: If the identifier is not the documented type.
    """
    if identifier != "library.Widget":
        raise KeyError(identifier)
    return "widget.html#Widget", None


class TestReferenceFilters(unittest.TestCase):
    """
    Check reference resolution, labels, optional targets, and escaping.
    """

    def test_short_and_full_labels(self) -> None:
        """
        Resolve abbreviated and full labels to the same target.
        """
        for brief, label in ((True, "Widget"), (False, "library.Widget")):
            with self.subTest(brief=brief):
                html, missing = fix_refs(
                    str(do_crossref(path="library.Widget", brief=brief)), _target_url
                )
                self.assertEqual([], missing)
                self.assertIn('href="widget.html#Widget"', html)
                self.assertIn(f">{label}</a>", html)
                if brief:
                    self.assertRegex(html, r'title="[^"]*library\.Widget[^"]*"')

    def test_missing_target_hover(self) -> None:
        """
        Keep an unknown type visible with its full identifier as a tooltip.
        """
        html, missing = fix_refs(str(do_crossref(path="external.Unknown")), _target_url)
        self.assertEqual([], missing)
        self.assertEqual('<span title="external.Unknown">Unknown</span>', html)

    def test_attribute_and_label_escaping(self) -> None:
        """
        Escape quotes and HTML syntax in reference attributes and labels.
        """
        html = str(do_crossref(path='library.<Widget & "label">', brief=False))
        self.assertIn('identifier="library.&lt;Widget &amp; &#34;label&#34;&gt;"', html)
        self.assertNotIn("<Widget", html)
        self.assertNotIn("<span data-autorefs-", html)

    def test_multiple_names_and_punctuation(self) -> None:
        """
        Resolve names while preserving and escaping non-name expression text.
        """
        html, missing = fix_refs(
            str(do_multi_crossref(text="library.Widget {Unknown} & <Other>")),
            _target_url,
        )
        self.assertEqual([], missing)
        self.assertTrue(html.startswith("<code>"))
        self.assertTrue(html.endswith("</code>"))
        self.assertIn('href="widget.html#Widget"', html)
        self.assertIn('{<span title="Unknown">Unknown</span>}', html)
        self.assertIn('&amp; &lt;<span title="Other">Other</span>&gt;', html)

    def test_without_code_wrapper(self) -> None:
        """
        Allow references in surrounding prose without a code wrapper.
        """
        html = str(do_multi_crossref(text="library.Widget", code=False))
        self.assertTrue(html.startswith("<autoref "))
        self.assertNotIn("<code>", html)


class TestExpressions(unittest.TestCase):
    """
    Render Griffe name leaves and compound annotations without recursive loops.
    """

    def test_name_reference(self) -> None:
        """
        Render a Griffe name with a canonical identifier and its authored label.
        """
        handler = get_handler()
        expression = ExprName(name="Widget", parent="library")
        html = handler.env.get_template("expression.html").render(expression=expression)
        resolved, missing = fix_refs(html, _target_url)
        self.assertEqual([], missing)
        self.assertIn('href="widget.html#Widget"', resolved)
        self.assertIn(">Widget</a>", resolved)

    def test_compound_expression(self) -> None:
        """
        Preserve compound annotation syntax and resolve its nested type name.
        """
        handler = get_handler()
        expression = ExprSubscript(
            left=ExprName(name="list"),
            slice=ExprName(name="Widget", parent="library"),
        )
        html = handler.env.get_template("expression.html").render(expression=expression)
        resolved, missing = fix_refs(html, _target_url)
        self.assertEqual([], missing)
        self.assertIn('<span title="list">list</span>[', resolved)
        self.assertIn('href="widget.html#Widget"', resolved)
        self.assertTrue(resolved.endswith("]"))

    def test_literal_defaults(self) -> None:
        """
        Keep default values as escaped literals rather than type references.
        """
        handler = get_handler()
        for value in ('"Widget"', "True", "0", "<literal>"):
            with self.subTest(value=value):
                html = handler.env.get_template("expression.html").render(
                    expression=value
                )
                self.assertNotIn("<autoref ", html)
                self.assertNotIn("<literal>", html)
                self.assertEqual(value, unescape(html))
