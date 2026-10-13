# Showcase

This demonstration module summarizes numeric values in a one-dimensional array, such as values
collected by a spreadsheet macro. It is a self-contained sample, rather than code from a production project.

Pass real numeric values: blanks, strings (including numeric strings), Boolean values, and errors are ignored.

```vb
Dim values As Variant
values = Array(12, Empty, "pending", 8)
Debug.Print SumNumbers(values)    ' 20
Debug.Print CountNumbers(values)  ' 2
```

## Rendered documentation

The documentation below is generated directly from the module's comments and signatures.
Follow the procedure links or expand a source block to inspect the result.

::: examples/showcase/src/ArraySummary.bas
    handler: vba
    options:
      heading_level: 3
      members_order: source
      show_source: true
      show_root_toc_entry: false
      docstring_section_style: list

## Source

Import this module into your VBA project, or copy the procedures from the listing.
[Download ArraySummary.bas](https://raw.githubusercontent.com/mkdocstrings/vba/master/examples/showcase/src/ArraySummary.bas).

```vb
--8<-- "examples/showcase/src/ArraySummary.bas"
```
