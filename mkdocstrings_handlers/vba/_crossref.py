import re

from markupsafe import Markup


def do_crossref(path: str, brief: bool = True) -> Markup:
    """Filter to create cross-references.

    Parameters:
        path: The path to link to.
        brief: Show only the last part of the path, add the full path as hover.

    Returns:
        Markup text.
    """
    full_path = path
    if brief:
        path = full_path.split(".")[-1]
    return Markup(
        "<span data-autorefs-optional-hover={full_path}>{path}</span>"
    ).format(full_path=full_path, path=path)


def do_multi_crossref(text: str, code: bool = True) -> Markup:
    """Filter to create cross-references.

    Parameters:
        text: The text to scan.
        code: Whether to wrap the result in a code tag.

    Returns:
        Markup text.
    """
    group_number = 0
    variables = {}

    def repl(match: re.Match[str]) -> str:
        nonlocal group_number
        group_number += 1
        path = match.group()
        path_var = f"path{group_number}"
        variables[path_var] = path
        return (
            f"<span data-autorefs-optional-hover={{{path_var}}}>{{{path_var}}}</span>"
        )

    text = re.sub(r"([\w.]+)", repl, text)
    if code:
        text = f"<code>{text}</code>"
    return Markup(text).format(**variables)
