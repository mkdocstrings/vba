import doctest
import unittest

from locate import this_dir

repo_dir = this_dir().parent


def load_tests(loader, tests, ignore):
    """
    See https://docs.python.org/3/library/doctest.html#unittest-api
    """
    modules = find_modules_with_doctests()
    for module in modules:
        tests.addTests(doctest.DocTestSuite(module))
    return tests


def find_modules_with_doctests():
    modules = []
    skip_n_parts = len(repo_dir.parts)
    for path in repo_dir.joinpath("mkdocstrings_handlers").rglob("*.py"):
        if path.name == "__init__.py":
            continue

        module = ".".join(path.parts[skip_n_parts:])
        module = module[:-3]
        modules.append(module)
    return modules


if __name__ == "__main__":
    unittest.main(
        failfast=True,
    )
