import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from locate import this_dir
from mkdocs.commands.build import build
from mkdocs.config import load_config

repo_dir = this_dir().parent
examples_dir = repo_dir.joinpath("examples")


@contextmanager
def tmp_build(config_file_path: Path):
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        with config_file_path.open(mode="rb") as f:
            config = load_config(config_file=f)
            config["site_dir"] = tmp_dir
            build(
                config=config,
                dirty=False,
                live_server=False,
            )

        try:
            yield tmp_dir
        finally:
            pass


class TestExamples(unittest.TestCase):
    def test_example1(self):
        raise unittest.SkipTest

        with tmp_build(examples_dir.joinpath("example1", "mkdocs.yml")) as tmp_dir:
            pass


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )
