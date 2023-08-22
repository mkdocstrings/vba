import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

from locate import this_dir
from mkdocs.commands.build import build
from mkdocs.config import load_config

repo_dir = this_dir().parent
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
    def test_example1(self):
        with tmp_build(examples_dir.joinpath("example1", "mkdocs.yml")) as tmp_dir:
            # TODO: Write assertions. For now, just check that it does not fail.
            pass


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )
