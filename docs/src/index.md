# mkdocstrings-vba

Generate documentation from comments in exported VBA modules (`.bas`) and classes (`.cls`).
Use it with [Zensical](https://zensical.org/) or MkDocs Material.
See the [live showcase](showcase.md) for rendered signatures, parameters, return values, and source code.

## Installation

These docs describe the development version on `master`, including support for Zensical.
PyPI version 0.0.10 does not include these changes. Until a matching release is available,
install this source revision with Python 3.11 or newer and Git:

```shell
python -m pip install "zensical==0.0.70" "mkdocstrings==1.0.7" "mkdocstrings-vba @ git+https://github.com/mkdocstrings/vba.git@2dfdf0fa1d0e55eac8b3a97abc0a21fe1bac5696"
```

For MkDocs Material, install the same source revision with its `material` extra:

MkDocs Material can also be used with Python 3.9 or newer.

```shell
python -m pip install "mkdocstrings==1.0.7" "mkdocstrings-vba[material] @ git+https://github.com/mkdocstrings/vba.git@2dfdf0fa1d0e55eac8b3a97abc0a21fe1bac5696"
```

## Your first page

Create this layout:

```text
my-project/
  mkdocs.yml
  docs/
    index.md
  src/
    Numbers.bas
```

Save this as `mkdocs.yml`:

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

Zensical provides its own theme; the `material` setting also lets MkDocs Material use this configuration.

Save this as `src/Numbers.bas`:

```vb
Public Function DoubleValue(ByVal value As Double) As Double
    ' Double a number.
    '
    ' Args:
    '     value: The number to double.
    '
    ' Returns:
    '     Twice the input value.
    DoubleValue = value * 2
End Function
```

Save this as `docs/index.md`:

```markdown
# Numbers

::: src/Numbers.bas
    handler: vba
```

From `my-project`, run `zensical serve` and open the local URL it prints.
Run `zensical build` to generate the HTML site in `site/`.
With MkDocs Material, use `mkdocs serve` and `mkdocs build` instead.

Continue with [Usage](usage.md) for comment syntax and configuration.
