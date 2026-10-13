# Usage

## Documentation comments

Place a procedure's documentation immediately after its signature, using apostrophe comments.
Continue each paragraph and section with consecutive comment lines; use a lone apostrophe for a blank line.
For module documentation, put the comment block at the start of the file,
after any exported `Attribute` lines and before `Option` statements.

Use [Google-style sections](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods):

- `Args:` describes parameters.
- `Returns:` describes the result of a function or `Property Get`.
- `Examples:` shows how to call the procedure.

Types come from the VBA signature. Parameter names match without regard to case.
An omitted parameter type or function return type is shown as `Variant`.
Explicit docstring type annotations are also preserved.

See [the showcase source](showcase.md#source) for a complete module.

## Source files and encoding

Each directive identifies one exported VBA file. Paths are relative to `mkdocs.yml`,
regardless of which Markdown page contains the directive:

```markdown
::: src/Numbers.bas
    handler: vba
```

Sources are read as Latin-1 by default. For UTF-8 source files, configure:

```yaml
plugins:
  - autorefs
  - mkdocstrings:
      handlers:
        vba:
          encoding: utf-8
```

Export modules from the VBA editor before building the docs.
The handler reads text files; it does not open Office documents or execute VBA.

## Links between procedures

In a documentation comment or Markdown page, use `[SumNumbers][]` to link to a documented procedure,
or `[custom link text][SumNumbers]` to change the label.
Both procedures must be included in the site. Use distinct procedure names to avoid ambiguous links.

## Rendering options

Set defaults under `handlers.vba.options`:

```yaml
plugins:
  - autorefs
  - mkdocstrings:
      handlers:
        vba:
          options:
            members_order: source
            show_source: true
```

Override options for one directive:

```markdown
::: src/Numbers.bas
    handler: vba
    options:
      heading_level: 3
      show_source: false
```

| Option | Default | Purpose |
| --- | --- | --- |
| `heading_level` | `2` | Set the initial heading level. |
| `members_order` | `alphabetical` | Order procedures by name or by `source` position. |
| `show_source` | `true` | Include expandable procedure source. |
| `show_signature` | `true` | Display procedure signatures. |
| `separate_signature` | `false` | Put each signature in its own code block. |
| `show_root_heading` | `false` | Display a heading for the module. |
| `show_if_no_docstring` | `false` | Include undocumented procedures. |
| `docstring_section_style` | `table` | Render sections as `table`, `list`, or `spacy`. |

## Compatibility and limits

The development handler requires Python 3.9 or newer, `mkdocstrings>=0.30,<2`, and `griffe>=1.3.1,<2`.
Zensical 0.0.70 is checked with mkdocstrings 0.30.1 and 1.0.7, without MkDocs Material installed.
Zensical itself requires Python 3.11 or newer.
MkDocs Material 9.x is also supported.

For mkdocstrings 0.30.0 or 0.30.1, use `pymdown-extensions<12.2`;
with Zensical and mkdocstrings 0.30.1, use `pymdown-extensions>=11,<12.2`.
The getting-started commands use mkdocstrings 1.0.7, which supports PyMdown 12.2.

The handler documents procedures and their comments, rather than providing a complete VBA language reference.
It supports ordinary `As` annotations, but does not interpret `DefType` statements or type suffixes.
`Sub`, `Property Let`, and `Property Set` have no return type.
