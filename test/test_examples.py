"""
Build example sites and check their documentation and assets.
"""

import unittest
import warnings
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

from mkdocs.commands.build import build
from mkdocs.config import load_config

from test.helpers import assert_no_warnings
from test.site_checks import (
    check_assets_and_links,
    check_crossrefs,
    check_example1,
    check_source,
)

repo_dir = Path(__file__).resolve().parent.parent
examples_dir = repo_dir / "examples"


@contextmanager
def tmp_build(config_file_path: Path) -> Generator[Path, None, None]:
    """
    Build an example into a temporary site directory.

    Args:
        config_file_path: MkDocs configuration file for the example.

    Yields:
        The site directory, available until the context exits.
    """
    with TemporaryDirectory() as temporary:
        site = Path(temporary)
        with config_file_path.open(mode="rb") as config_file:
            config = load_config(config_file=config_file)
        config["site_dir"] = site
        build(config=config)
        yield site


class TestExamples(unittest.TestCase):
    """
    Check example output using the same assertions as installed-package CI.
    """

    def test_source_display(self) -> None:
        """
        Render original source, physical line numbers, and matching terminators.
        """
        with assert_no_warnings():
            with tmp_build(examples_dir / "example3" / "mkdocs.yml") as site:
                check_source(site=site, source=examples_dir / "example3/src")
                check_assets_and_links(site=site, builder="mkdocs")

    def test_example1(self) -> None:
        """
        Render signatures, documentation sections, anchors, source, and styles.
        """
        with assert_no_warnings():
            with tmp_build(examples_dir / "example1" / "mkdocs.yml") as site:
                check_example1(site=site)
                check_assets_and_links(site=site, builder="mkdocs")

    def test_crossrefs(self) -> None:
        """
        Resolve explicit and generated references without legacy markers or warnings.
        """
        with warnings.catch_warnings(), assert_no_warnings():
            warnings.filterwarnings(
                "error",
                message="autorefs .*span.*deprecated",
                category=DeprecationWarning,
            )
            with tmp_build(examples_dir / "example2" / "mkdocs.yml") as site:
                check_crossrefs(site=site, source=examples_dir / "example2/src")
                check_assets_and_links(site=site, builder="mkdocs")


if __name__ == "__main__":
    unittest.main(failfast=True)
