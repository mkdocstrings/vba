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

## Usage

Configure the handler in `mkdocs.yml`, which Zensical and MkDocs Material support:

```yaml
plugins:
  - autorefs
  - mkdocstrings:
      handlers:
        vba: {}
```

Document a VBA file from a Markdown page:

```markdown
::: src/example.bas
    handler: vba
```

Source paths are relative to the configuration file. Sources are read as Latin-1 by default;
set `encoding: utf-8` under `handlers.vba` for UTF-8 files.

Place Google-style documentation comments directly after the procedure signature:

```vb
Public Function choose(value, Optional fallback = 2)
    ' Choose a value.
    '
    ' Args:
    '     value: The preferred value.
    '     fallback: The fallback value.
    '
    ' Returns:
    '     The selected value.
    choose = value
End Function
```

Parameter names match without regard to case. Omitted parameter types and omitted
`Function`/`Property Get` return types are documented as `Variant`.
Explicit signature types and docstring annotations are preserved.
`Sub` and `Property Let` have no return type.

The parser supports ordinary `As` annotations; it does not interpret `DefType` statements or type suffixes.
Zensical and MkDocs Material include the bundled VBA styles automatically.

## Compatibility

Requires Python 3.9 or newer, `mkdocstrings>=0.30,<2`, and `griffe>=1.3.1,<2`.

| Builder         | Versions checked                          | mkdocstrings versions checked |
|-----------------|-------------------------------------------|-------------------------------|
| MkDocs Material | 9.2.1 and current 9.x                     | 0.30.0, 0.30.1, 1.0.7         |
| Zensical        | 0.0.70, without MkDocs Material installed | 0.30.1, 1.0.7                 |

With mkdocstrings 0.30.0 or 0.30.1, install `pymdown-extensions<12.2`.
For Zensical with mkdocstrings 0.30.1, use `pymdown-extensions>=11,<12.2`.
mkdocstrings 1.0.7 supports PyMdown 12.2.

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
