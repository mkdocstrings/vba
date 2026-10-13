"""
Check example sites from either builder, including installed-distribution builds.
"""

from __future__ import annotations

import argparse
import re
from html import unescape
from html.parser import HTMLParser
from importlib import import_module
from importlib.resources import files
from pathlib import Path
from urllib.parse import unquote, urlsplit


class _Page(HTMLParser):
    """
    Collect local links, anchors, and stylesheet references from an HTML page.
    """

    def __init__(self) -> None:
        """
        Initialize an empty page inventory.
        """
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Record the references and anchor of an HTML element.

        Args:
            tag: Element name.
            attrs: Element attributes from the HTML parser.
        """
        attributes = dict(attrs)
        identifier = attributes.get("id")
        if identifier is not None:
            self.ids.add(identifier)
        for name in ("href", "src"):
            value = attributes.get(name)
            if value is not None:
                self.links.append(value)
        href = attributes.get("href")
        if tag == "link" and attributes.get("rel") == "stylesheet" and href is not None:
            self.stylesheets.append(href)


def _read_page(*, path: Path) -> _Page:
    """
    Read an HTML page's links and anchors.

    Args:
        path: Generated HTML file.

    Returns:
        The parsed page inventory.
    """
    page = _Page()
    page.feed(path.read_text(encoding="utf-8"))
    return page


def check_assets_and_links(*, site: Path, builder: str) -> None:
    """
    Check handler CSS, local assets, page links, and fragment targets.

    Args:
        site: Built site directory.
        builder: Either mkdocs or zensical.
    """
    bundled_css = (
        files("mkdocstrings_handlers.vba")
        .joinpath("templates/material/style.css")
        .read_text(encoding="utf-8")
        .strip()
    )
    for path in site.rglob("*.html"):
        if path.name == "404.html":
            continue
        html = path.read_text(encoding="utf-8")
        page = _read_page(path=path)
        assert page.stylesheets, path
        assert "<autoref " not in html and "data-autorefs-" not in html, path
        if builder == "zensical":
            styles = re.findall(
                r"<style data-mkdocstrings-vba[^>]*>(.*?)</style>", html, re.DOTALL
            )
            assert styles and all(
                style.strip() == bundled_css for style in styles
            ), path
        else:
            assert "data-mkdocstrings-vba" not in html, path
            assert bundled_css in (site / "assets/_mkdocstrings.css").read_text(
                encoding="utf-8"
            )
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if not url.path:
                target = path
            elif url.path.startswith("/"):
                target = site / unquote(url.path).lstrip("/")
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


def check_example1(*, site: Path) -> None:
    """
    Check the basic example's signatures, documentation sections, and source blocks.

    Args:
        site: Built example1 site directory.
    """
    html = (site / "index.html").read_text(encoding="utf-8")
    fenced = next(
        (
            block
            for block in re.finditer(
                r"<pre\b[^>]*>.*?<code\b[^>]*>(.*?)</code>.*?</pre>", html, re.DOTALL
            )
            if unescape(re.sub(r"<[^>]+>", "", block[1])).strip()
            == 'MsgBox "Hello from VBA"'
        ),
        None,
    )
    assert fenced is not None
    assert html.index("Render a fenced VBA example:") < fenced.start()
    assert fenced.end() < html.index("Continue with explanatory text.")
    text = " ".join(unescape(re.sub(r"<[^>]+>", "", html)).split())
    assert (
        "Function fuzz_HotelEcho_helper(WS As Worksheet, Name As String, description As String)"
        in text
    )
    assert "Public Property Get asdf()" in text
    assert "Public Property Let asdf(ByVal vNewValue As Variant)" in text
    for phrase in (
        "Parameters:",
        "Returns:",
        "Examples:",
        "Render a fenced VBA example:",
        'MsgBox "Hello from VBA"',
        "Continue with explanatory text.",
        "The worksheet",
        "A fancy ListObject",
        "This is it!",
    ):
        assert phrase in text, phrase
    for identifier in (
        "fuzz_HotelEcho_helper",
        "asdf123QwerZxcv_yuio",
        "dolf",
        "asdf",
        "iHaveADocString",
    ):
        assert f'id="{identifier}"' in html, identifier
    blocks = re.findall(r'<details class="quote">(.*?)</details>', html, re.DOTALL)
    function_source = next(
        block for block in blocks if "Function fuzz_HotelEcho_helper( _" in block
    )
    assert "End Function" in function_source
    for kind in ("Get", "Let"):
        property_source = next(
            block for block in blocks if f"Public Property {kind} asdf(" in block
        )
        assert "End Property" in property_source


def check_crossrefs(*, site: Path, source: Path) -> None:
    """
    Check explicit references, type references, implicit types, and stable anchors.

    Args:
        site: Built example2 site directory.
        source: Original example2 source directory.
    """
    html = (site / "index.html").read_text(encoding="utf-8")
    widget = (site / "widget.html").read_text(encoding="utf-8")
    assert html.count('href="widget.html#Widget"') >= 3
    assert 'href="widget.html#reset"' in html
    assert 'title="MissingType"' in html
    assert "<code>VALUE</code>" in html and "<code>LABEL</code>" in html
    assert '"Widget, label"' in {
        unescape(re.sub(r"<[^>]+>", "", code)).strip()
        for code in re.findall(r"<code[^>]*>(.*?)</code>", html, re.DOTALL)
    }
    choose_value, current_value = html.split('id="chooseValue"', 1)[1].split(
        'id="currentValue"', 1
    )
    assert choose_value.count("<code>Variant</code>") == 3
    assert current_value.count("<code>Variant</code>") == 1
    assert (
        "Public Function chooseValue(value, Optional fallback = 2)</code>"
        in choose_value
    )
    assert "Public Property Get currentValue()</code>" in current_value
    assert 'id="makeWidget"' in html and 'id="reset"' in widget
    for identifier in ("item", "item--let", "item--set"):
        assert widget.count(f'id="{identifier}"') == 1
        assert f'href="widget.html#{identifier}"' in html
    module_id = (source / "Widget.cls").as_posix()
    module_ids = {module_id}
    if source.drive:
        # Zensical's Rust canonicalization uses extended-length paths on Windows.
        module_ids.add("//?/" + module_id)
    assert _read_page(path=site / "widget.html").ids & module_ids


def check_source(*, site: Path, source: Path) -> None:
    """
    Compare rendered source and line numbers with the original VBA file.

    Args:
        site: Built example3 site directory.
        source: Original example3 source directory.
    """
    html = (site / "index.html").read_text(encoding="utf-8")
    code_blocks = [
        unescape(re.sub(r"<[^>]+>", "", code)).rstrip("\n")
        for code in re.findall(r"<code[^>]*>(.*?)</code>", html, re.DOTALL)
    ]
    assert (
        "Public Function chooseValue( _\n    value As Long, _\n"
        "    Optional fallback As Long = 2) _\n    As Long"
    ) in code_blocks
    lines = (source / "source.bas").read_text(encoding="utf-8").splitlines()
    blocks = re.findall(r'<details class="quote">(.*?)</details>', html, re.DOTALL)
    assert len(blocks) == 2
    for block, first, last in zip(blocks, (6, 25), (23, 31)):
        code = re.search(r"<code[^>]*>(.*?)</code>", block, re.DOTALL)
        assert code is not None
        assert (
            unescape(re.sub(r"<[^>]+>", "", code[1])).splitlines()
            == lines[first - 1 : last]
        )
        numbers = re.findall(r'<span class="normal">\s*(\d+)</span>', block)
        assert [int(n) for n in numbers] == list(range(first, last + 1))


def check_installed_package() -> None:
    """
    Verify the installed package provides its templates, CSS, and typing markers.
    """
    package = import_module("mkdocstrings_handlers.vba")
    assert package.__file__ is not None
    assert "site-packages" in Path(package.__file__).parts, package.__file__
    for name in ("mkdocstrings_handlers", "mkdocstrings_handlers.vba"):
        assert files(name).joinpath("py.typed").is_file(), name
    for name in (
        "module.html",
        "_base/procedure.html",
        "_base/expression.html",
        "docstring/parameters.html",
        "style.css",
    ):
        assert (
            files("mkdocstrings_handlers.vba")
            .joinpath(f"templates/material/{name}")
            .is_file()
        ), name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("examples", type=Path)
    parser.add_argument("--builder", choices=("mkdocs", "zensical"), required=True)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    root = args.examples.resolve()
    if args.installed:
        check_installed_package()
    check_example1(site=root / "example1/site")
    check_crossrefs(site=root / "example2/site", source=root / "example2/src")
    check_source(site=root / "example3/site", source=root / "example3/src")
    for name in ("example1", "example2", "example3"):
        check_assets_and_links(site=root / name / "site", builder=args.builder)
    print("Checked signatures, documentation, anchors, source, CSS, and local links.")
