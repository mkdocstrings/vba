# mkdocstrings-vba

A VBA handler for [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) and [Zensical](https://zensical.org/).

Since there is no official way of documenting VBA functions, we have opted for
the [Google Docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) commonly used
in Python projects. This is conveniently parsed by the [`griffe`](https://mkdocstrings.github.io/griffe) library which
is also used by [`mkdocstrings[python]`](https://mkdocstrings.github.io/python/). The argument types and return types
are taken from the
VBA [Function](https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/function-statement)
or [Sub](https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/sub-statement) signatures,
which we parse using [regex](https://regular-expressions.info).

## Installation

For Zensical:

```shell
python -m pip install zensical mkdocstrings-vba
```

For MkDocs Material:

```shell
python -m pip install "mkdocstrings-vba[material]"
```

The `material` extra installs the MkDocs Material theme.
Zensical uses its own theme and does not need this extra.

## Examples

See the [`examples`](https://github.com/mkdocstrings/vba/tree/master/examples) folder.

To build an example site:

1. `python -m pip install "mkdocstrings-vba[material]"`
2. `cd examples/example1`
3. View the source code.
4. `mkdocs build`
5. cd `site/`
6. View the results.

For Zensical, use the Zensical installation above and run `zensical build` in the same example folder.

## Running tests

Use Python 3.12 or newer for development.

```shell
python -m pip install --upgrade pip
python -m pip install --group dev -e .
python -m unittest
```

This will run all tests. This includes

- Unit tests from `test/`.
- Doctests from `mkdocstrings_handlers/vba/`.
- Full builds from `examples/`.

## Linting

Fix code style using `black`:

```shell
python -m black .
```

Check types using `mypy`:

```shell
python -m mypy
```

## Building distributions

```shell
python -m build
python -m twine check --strict dist/*
```
