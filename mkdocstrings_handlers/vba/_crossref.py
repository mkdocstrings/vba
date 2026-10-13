import re
from typing import Any

from griffe import ExprName
from markupsafe import Markup, escape

_builtin_types = {
    "any",
    "boolean",
    "byte",
    "currency",
    "date",
    "decimal",
    "double",
    "error",
    "integer",
    "long",
    "longlong",
    "longptr",
    "object",
    "single",
    "string",
    "variant",
}


def do_vba_annotation(annotation: Any) -> Any:
    """
    Make inferred custom VBA types available to the expression cross-reference template.

    Args:
        annotation: A signature type string or an already parsed Griffe annotation.

    Returns:
        A referenceable custom type, or the unchanged built-in/parsed annotation.
    """
    if (
        isinstance(annotation, str)
        and annotation.casefold() not in _builtin_types
        and re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", annotation
        )
    ):
        return ExprName(name=annotation, parent=None)
    return annotation


def do_crossref(path: str, brief: bool = True) -> Markup:
    """
    Create an optional cross-reference.

    Args:
        path: The path to link to.
        brief: Show only the last part of the path, add the full path as hover.

    Returns:
        Markup text.
    """
    full_path = path
    if brief:
        path = full_path.split(".")[-1]
    return Markup('<autoref identifier="{full_path}" optional>{path}</autoref>').format(
        full_path=full_path, path=path
    )


def do_multi_crossref(text: str, code: bool = True) -> Markup:
    """
    Cross-reference names in an expression while escaping surrounding text.

    Args:
        text: The text to scan.
        code: Whether to wrap the result in a code tag.

    Returns:
        Markup text.
    """
    parts = []
    previous = 0
    for match in re.finditer(r"[\w.]+", text):
        parts.append(escape(text[previous : match.start()]))
        parts.append(do_crossref(path=match.group(), brief=False))
        previous = match.end()
    parts.append(escape(text[previous:]))
    result = Markup("").join(parts)
    if code:
        return Markup("<code>{}</code>").format(result)
    return result
