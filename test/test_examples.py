import unittest
import warnings
from contextlib import contextmanager
from logging import WARNING
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

from mkdocs.commands.build import build
from mkdocs.config import load_config

repo_dir = Path(__file__).resolve().parent.parent
examples_dir = repo_dir.joinpath("examples")


@contextmanager
def tmp_build(config_file_path: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        with config_file_path.open(mode="rb") as f:
            config = load_config(config_file=f)
            config["site_dir"] = tmp_dir
            build(config=config)

        try:
            yield tmp_dir
        finally:
            pass


class TestExamples(unittest.TestCase):
    def test_example1(self) -> None:
        with self.assertNoLogs(level=WARNING):
            with tmp_build(examples_dir.joinpath("example1", "mkdocs.yml")) as tmp_dir:
                # TODO: Write assertions. For now, just check that it does not fail.
                pass

    def test_crossrefs(self) -> None:
        """
        Resolve VBA and type references across pages without legacy markers or warnings.
        """
        with warnings.catch_warnings(), self.assertNoLogs(level=WARNING):
            warnings.filterwarnings(
                "error",
                message="autorefs .*span.*deprecated",
                category=DeprecationWarning,
            )
            with tmp_build(examples_dir / "example2" / "mkdocs.yml") as site:
                html = (site / "index.html").read_text(encoding="utf-8")
                widget = (site / "widget.html").read_text(encoding="utf-8")
        self.assertGreaterEqual(html.count('href="widget.html#Widget"'), 3)
        self.assertIn('href="widget.html#reset"', html)
        self.assertIn('title="MissingType"', html)
        self.assertNotIn("<autoref ", html)
        self.assertNotIn("data-autorefs-", html)
        self.assertIn('id="makeWidget"', html)
        self.assertIn('id="reset"', widget)
        module_id = (examples_dir / "example2" / "src" / "Widget.cls").as_posix()
        self.assertIn(f'id="{module_id}"', widget)


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )
