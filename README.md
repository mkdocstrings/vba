# mkdocstrings-vba

A VBA handler for [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings).

Since there is no official way of documenting VBA functions, we have opted for
the [Google Docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) commonly used
in Python projects. This is conveniently parsed by the [`griffe`](https://mkdocstrings.github.io/griffe) library which
is also used by [`mkdocstrings[python]`](https://mkdocstrings.github.io/python/). The argument types and return types
are taken from the
VBA [Function](https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/function-statement)
or [Sub](https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/sub-statement) signatures,
which we parse using [regex](https://regular-expressions.info).

## Examples

See the [`examples`](examples) folder.

To build an example site:

1. `pip install mkdocstrings mkdocstrings-vba`
2. `cd examples/example1`
3. View the source code.
4. `mkdocs build`
5. cd `site/`
6. View the results.

## Running tests

```shell
pip install -r test-requirements.txt
python -m unittest
```

This will run all tests. This includes
- Unit tests from `tests/`.
- Doctests from `mkdocstrings_vba/`.
- Full builds from `examples/`.
