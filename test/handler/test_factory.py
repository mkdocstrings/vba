"""
Test the handler factory and configuration passed by mkdocstrings.
"""

import unittest
import warnings
import re
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType, SimpleNamespace
from typing import Any

from markdown.extensions.toc import TocExtension
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocstrings import Handlers

from mkdocstrings_handlers.vba import get_handler
from mkdocstrings_handlers.vba._handler import VbaHandler
from mkdocstrings_handlers.vba._types import VbaModuleInfo


class TestFactory(unittest.TestCase):
    """
    Check factory calls with direct and SSG-provided configuration.
    """

    def test_default_configuration(self) -> None:
        """
        Construct a handler without deprecated arguments or missing Markdown settings.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            handler = get_handler()
        self.assertEqual(Path.cwd(), handler.base_dir)
        self.assertEqual("latin1", handler.encoding)
        self.assertEqual("material", handler.theme)
        self.assertIsNone(handler.custom_templates)
        self.assertEqual((), handler.mdx)
        self.assertEqual({}, handler.mdx_config)

    def test_tool_configurations(self) -> None:
        """
        Resolve relative VBA paths beside mapping and attribute-based configuration files.
        """
        with TemporaryDirectory() as temporary:
            config_dir = Path(temporary) / "configuration"
            config_dir.mkdir()
            source = config_dir / "source.bas"
            source.write_bytes(b"' Caf\xe9")
            for filename in ("mkdocs.yml", "zensical.toml"):
                config_file = config_dir / filename
                mkdocs_config = MkDocsConfig(config_file_path=str(config_file))
                configurations = (
                    {"config_file_path": str(config_file)},
                    MappingProxyType({"config_file_path": str(config_file)}),
                    SimpleNamespace(config_file_path=str(config_file)),
                    mkdocs_config,
                )
                for config in configurations:
                    with self.subTest(filename=filename, config=type(config).__name__):
                        handler = get_handler(tool_config=config)
                        module = handler.collect(identifier="source.bas", config={})
                        self.assertEqual(source, module.path)
                        self.assertEqual(["' Café"], module.source)

    def test_missing_config_path(self) -> None:
        """
        Fall back to the working directory when the tool supplies no config path.
        """
        for config in (None, {}, {"config_file_path": None}, SimpleNamespace()):
            with self.subTest(config=config):
                self.assertEqual(Path.cwd(), get_handler(tool_config=config).base_dir)

    def test_markdown_configuration(self) -> None:
        """
        Forward Markdown extension instances and configuration without recreating them.
        """
        extension = TocExtension(permalink=True)
        extensions = [extension]
        configuration = {"toc": {"toc_depth": "2-3"}}
        handler = get_handler(mdx=extensions, mdx_config=configuration)
        self.assertIs(extensions, handler.mdx)
        self.assertIs(extension, handler.mdx[0])
        self.assertIs(configuration, handler.mdx_config)

    def test_none_markdown_configuration(self) -> None:
        """
        Normalize explicit missing Markdown settings to empty collections.
        """
        handler = get_handler(mdx=None, mdx_config=None)
        self.assertEqual((), handler.mdx)
        self.assertEqual({}, handler.mdx_config)

    def test_encoding_precedence(self) -> None:
        """
        Prefer an explicit encoding over handler configuration and the Latin-1 default.
        """
        for explicit, configured, expected in (
            (None, {}, "latin1"),
            (None, {"encoding": "utf-8"}, "utf-8"),
            ("latin1", {"encoding": "utf-8"}, "latin1"),
        ):
            with self.subTest(explicit=explicit, configured=configured):
                handler = get_handler(encoding=explicit, handler_config=configured)
                self.assertEqual(expected, handler.encoding)

    def test_handler_manager(self) -> None:
        """
        Accept the complete factory call made by the public handler manager.
        """
        manager = Handlers(
            theme="material",
            default="vba",
            inventory_project="test",
            handlers_config={
                "vba": {"encoding": "utf-8", "options": {"show_source": False}}
            },
            tool_config=SimpleNamespace(config_file_path=None),
        )
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", DeprecationWarning)
                handler = manager.get_handler("vba")
            assert isinstance(handler, VbaHandler)
            self.assertEqual("utf-8", handler.encoding)
            self.assertFalse(handler.get_options({})["show_source"])
        finally:
            manager.teardown()

    def test_unused_factory_arguments(self) -> None:
        """
        Keep additional factory arguments out of the base handler constructor.
        """
        handler = get_handler(future_setting="ignored", handler_config={})
        self.assertEqual("vba", handler.name)


class TestOptions(unittest.TestCase):
    """
    Check precedence and isolation of rendering options.
    """

    def test_option_precedence(self) -> None:
        """
        Apply directive options over global options and retain other defaults.
        """
        handler = get_handler(
            handler_config={"options": {"heading_level": 3, "show_source": False}}
        )
        options = handler.get_options({"heading_level": 4})
        self.assertEqual(4, options["heading_level"])
        self.assertFalse(options["show_source"])
        self.assertTrue(options["show_signature"])

    def test_read_only_global_options(self) -> None:
        """
        Accept read-only mappings without modifying handler configuration.
        """
        options = MappingProxyType({"heading_level": 3})
        handler = get_handler(handler_config=MappingProxyType({"options": options}))
        self.assertEqual(3, handler.get_options({})["heading_level"])

    def test_option_isolation(self) -> None:
        """
        Isolate saved options and each directive, including nested custom template settings.
        """
        configured: dict[str, Any] = {
            "options": {"custom": {"labels": ["global"]}, "heading_level": 3}
        }
        local: dict[str, Any] = {"custom": {"labels": ["local"]}}
        original = deepcopy(configured)
        handler = get_handler(handler_config=configured)
        configured["options"]["heading_level"] = 6
        options = handler.get_options(local)
        options["custom"]["labels"].append("changed")
        options["show_source"] = False
        self.assertEqual(["local"], local["custom"]["labels"])
        self.assertEqual(original["options"]["custom"], configured["options"]["custom"])
        self.assertEqual(["local"], handler.get_options(local)["custom"]["labels"])
        self.assertEqual(["global"], handler.get_options({})["custom"]["labels"])
        self.assertEqual(3, handler.get_options({})["heading_level"])
        self.assertTrue(handler.get_options({})["show_source"])

    def test_render_preserves_options(self) -> None:
        """
        Leave caller-owned options unchanged when rendering more than once.
        """
        handler = get_handler()
        handler.update_env({})
        module = VbaModuleInfo(
            docstring=None, source=[], path=Path("empty.bas"), procedures=[]
        )
        options = handler.get_options({})
        original = deepcopy(options)
        handler.render(module, options)
        handler.render(module, options)
        self.assertEqual(original, options)


class TestConfiguredBuild(unittest.TestCase):
    """
    Exercise factory configuration through an actual MkDocs build.
    """

    def test_configured_rendering(self) -> None:
        """
        Render relative UTF-8 sources with global options, local overrides, and extensions.
        """
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            docs = root / "docs"
            docs.mkdir()
            (root / "first.bas").write_text(
                "' Café\n'\n' !!! note\n'     Configured admonition.\n\n"
                "Sub first()\n    ' First procedure.\nEnd Sub\n",
                encoding="utf-8",
            )
            (root / "second.bas").write_text(
                "Sub second()\n    ' Second procedure.\nEnd Sub\n", encoding="utf-8"
            )
            (docs / "index.md").write_text(
                "# Reference\n\n::: first.bas\n    handler: vba\n\n"
                "::: second.bas\n    handler: vba\n    options:\n"
                "      heading_level: 4\n      show_root_heading: false\n"
                "      show_source: true\n",
                encoding="utf-8",
            )
            config_file = root / "mkdocs.yml"
            config_file.write_text(
                "site_name: Factory configuration test\ntheme: material\n"
                "plugins:\n  - mkdocstrings:\n      handlers:\n        vba:\n"
                "          encoding: utf-8\n          options:\n"
                "            heading_level: 2\n            show_root_heading: true\n"
                "            show_source: false\n"
                "markdown_extensions:\n  - admonition\n  - toc:\n      permalink: true\n",
                encoding="utf-8",
            )
            with self.assertNoLogs(level="WARNING"):
                build(config=load_config(config_file=str(config_file)))
            html = (root / "site" / "index.html").read_text(encoding="utf-8")
            headings = {
                identifier: int(level)
                for level, identifier in re.findall(
                    r'<h([1-6])\b[^>]*id="([^"]+)"', html
                )
            }
            self.assertEqual(3, headings["first"])
            self.assertEqual(4, headings["second"])
            self.assertIn("Café", html)
            self.assertIn('class="admonition note"', html)
            self.assertIn('class="headerlink"', html)
            self.assertEqual(1, html.count("<summary>Source code</summary>"))
