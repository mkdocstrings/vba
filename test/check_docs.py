"""
Check the built documentation, its showcase, and links under the Pages project path.
"""

from __future__ import annotations

import argparse
import re
from html import unescape
from importlib.resources import files
from pathlib import Path
from urllib.parse import unquote, urlsplit

from test.site_checks import _read_page


def check_documentation(*, site: Path, source: Path) -> None:
    """
    Check the documentation pages and generated VBA showcase.

    Args:
        site: Directory containing the generated documentation site.
        source: Original VBA showcase module.
    """
    for name in ("index.html", "usage/index.html", "showcase/index.html"):
        assert (site / name).is_file(), name

    for path in site.rglob("*.html"):
        if path.name == "404.html":
            continue
        html = path.read_text(encoding="utf-8")
        page = _read_page(path=path)
        assert page.stylesheets, path
        assert "<autoref " not in html and "data-autorefs-" not in html, path
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if not url.path:
                target = path
            elif url.path.startswith("/"):
                assert url.path.startswith("/vba/"), (path, link)
                target = site / unquote(url.path.removeprefix("/vba/"))
            else:
                target = path.parent / unquote(url.path)
            if target.is_dir():
                target = target / "index.html"
            assert target.is_file(), (path, link)
            if url.fragment and target.suffix == ".html":
                assert unquote(url.fragment) in _read_page(path=target).ids, (
                    path,
                    link,
                )

    html = (site / "showcase/index.html").read_text(encoding="utf-8")
    text = " ".join(unescape(re.sub(r"<[^>]+>", "", html)).split())
    for phrase in (
        "Public Function SumNumbers(ByVal values As Variant)",
        "Public Function CountNumbers(ByVal values As Variant)",
        "Parameters:",
        "Returns:",
        "Examples:",
        "Double",
        "Long",
        "The sum of the numeric entries",
        "The number of numeric entries",
    ):
        assert phrase in text, phrase
    for name in ("SumNumbers", "CountNumbers"):
        assert f'id="{name}"' in html, name
        assert f'href="#{name}"' in html, name

    bundled_css = (
        files("mkdocstrings_handlers.vba")
        .joinpath("templates/material/style.css")
        .read_text(encoding="utf-8")
        .strip()
    )
    styles = re.findall(
        r"<style data-mkdocstrings-vba[^>]*>(.*?)</style>", html, re.DOTALL
    )
    assert styles and all(style.strip() == bundled_css for style in styles)
    assert "TODO" not in text
    examples = re.findall(
        r"<p><strong>Examples:</strong></p>(.*?)<details", html, re.DOTALL
    )
    assert len(examples) == 2
    for example, name in zip(examples, ("SumNumbers", "CountNumbers")):
        text = unescape(re.sub(r"<[^>]+>", "", example))
        assert f"Debug.Print {name}(" in text, name
    blocks = re.findall(r'<details class="quote">(.*?)</details>', html, re.DOTALL)
    assert len(blocks) == 2
    code = source.read_text(encoding="utf-8")
    for block, procedure in zip(blocks, ("SumNumbers", "CountNumbers")):
        rendered = re.search(r"<code[^>]*>(.*?)</code>", block, re.DOTALL)
        assert rendered is not None
        expected = re.search(
            rf"Public Function {procedure}\b.*?End Function", code, re.DOTALL
        )
        assert expected is not None
        actual = unescape(re.sub(r"<[^>]+>", "", rendered[1])).strip()
        assert actual == expected[0], procedure
    assert 'Attribute VB_Name = "ArraySummary"' in unescape(
        re.sub(r"<[^>]+>", "", html)
    ), "Missing source listing"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    check_documentation(
        site=args.site.resolve(),
        source=Path(__file__).resolve().parent.parent
        / "examples/showcase/src/ArraySummary.bas",
    )
    print(
        "Checked documentation pages, showcase output, source, styles, and local links."
    )
