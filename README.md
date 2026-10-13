# mkdocstrings-vba

A VBA handler for [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) and [Zensical](https://zensical.org/).

[Documentation](https://mkdocstrings.github.io/vba/) ·
[Live showcase](https://mkdocstrings.github.io/vba/showcase/)

## Quickstart

The development version supports Zensical. PyPI 0.0.10 does not include these changes;
install this source revision with Python 3.11 or newer and Git:

```shell
python -m pip install "zensical==0.0.70" "mkdocstrings==1.0.7" "mkdocstrings-vba @ git+https://github.com/mkdocstrings/vba.git@2dfdf0fa1d0e55eac8b3a97abc0a21fe1bac5696"
```

In `mkdocs.yml`:

```yaml
site_name: My VBA library
theme:
  name: material
plugins:
  - autorefs
  - mkdocstrings:
      handlers:
        vba: {}
```

In `docs/index.md`:

```markdown
# My VBA library

::: src/example.bas
    handler: vba
```

Export your VBA module to `src/example.bas` and place Google-style documentation comments directly after
each procedure signature. Source paths are relative to `mkdocs.yml`; Latin-1 is the default encoding.

Run `zensical serve` to preview or `zensical build` to generate the site.

See [Getting started](https://mkdocstrings.github.io/vba/) for a complete example and MkDocs Material installation,
or [Usage](https://mkdocstrings.github.io/vba/usage/) for configuration, compatibility, and parser limits.
More examples are in [`examples/`](https://github.com/mkdocstrings/vba/tree/master/examples).

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
