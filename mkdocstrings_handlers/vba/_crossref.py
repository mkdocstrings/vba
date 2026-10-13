import re

from markupsafe import Markup, escape


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
