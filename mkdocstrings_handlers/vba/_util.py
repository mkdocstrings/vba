import re
from typing import List, Generator, Optional, Tuple, Union

from griffe import Docstring, Function, Module, Parameters, Parameter, Parser

from ._regex import re_signature, re_arg
from ._types import (
    VbaArgumentInfo,
    VbaSignatureInfo,
    VbaProcedureInfo,
)


class _VbaParameters(Parameters):
    """
    Adapt Griffe's parameter lookup to VBA's case-insensitive names.
    """

    def __getitem__(self, name_or_index: Union[int, str]) -> Parameter:
        """
        Retrieve a parameter by position or case-insensitive name.

        Args:
            name_or_index: Position or name, optionally prefixed with Griffe's stars.

        Returns:
            The original parameter, retaining its declared spelling.

        Raises:
            IndexError: If the position is outside the parameter list.
            KeyError: If the name does not match any declared parameter.
        """
        if isinstance(name_or_index, int):
            return super().__getitem__(name_or_index)
        name = name_or_index.lstrip("*").casefold()
        for index in range(len(self)):
            parameter = super().__getitem__(index)
            if parameter.name.casefold() == name:
                return parameter
        raise KeyError(f"parameter {name_or_index} not found")

    def __contains__(self, param_name: str) -> bool:
        """
        Check whether a case-insensitive parameter name is declared.

        Args:
            param_name: Name, optionally prefixed with Griffe's stars.

        Returns:
            Whether a matching parameter exists.
        """
        try:
            self[param_name]
        except KeyError:
            return False
        return True


def is_signature(line: str) -> bool:
    """
    Check if the given line is the start of a signature of a sub, function or property.

    Examples:
        >>> is_signature("Function fuzz_HotelEcho_helper()")
        True
        >>> is_signature("private sub asdfQwerZxcv_yuio(fooBar As listObject)")
        True
        >>> is_signature("Sub iDoNotHaveADocString()")
        True
        >>> is_signature("Public Property Get asdf() As Variant")
        True
        >>> is_signature('Attribute VB_Name = "Module1"')
        False
        >>> is_signature("' This is the file docstring")
        False
    """
    try:
        parse_signature(line)
    except RuntimeError:
        return False

    return True


def is_comment(line: str) -> bool:
    """
    Check for an apostrophe comment, allowing space or tab indentation.

    Args:
        line: Original VBA source line.

    Returns:
        Whether the line starts with a comment after indentation.
    """
    return re.match(r"^[ \t]*'", line) is not None


def uncomment_lines(lines: List[str]) -> List[str]:
    return [line.replace("'", "", 1) for line in lines]


def _logical_lines(*, lines: List[str]) -> Generator[Tuple[str, int, int], None, None]:
    """
    Join continued statements while retaining their physical line boundaries.

    Args:
        lines: Original source lines without newline characters.

    Yields:
        Logical text and its inclusive, one-based first and last physical lines.
    """
    parts: List[str] = []
    first_line = 1
    for last_line, line in enumerate(lines, start=1):
        if not parts:
            first_line = last_line
        continuation = re.search(r" _[ \t]*$", line)
        if continuation is not None and last_line < len(lines) and not is_comment(line):
            parts.append(line[: continuation.start()] + " ")
            continue
        parts.append(line)
        yield "".join(parts), first_line, last_line
        parts = []


def find_file_docstring(code: str, *, parent: Optional[Module] = None) -> Docstring:
    """
    Collect module comments before the first procedure signature.

    Args:
        code: Original VBA source, including any continuation lines.
        parent: Griffe module providing the source path, when collecting a file.

    Returns:
        Module documentation with its original source location.
    """
    docstring_lines = []
    lineno = None
    endlineno = None
    lines = code.splitlines()

    for line, first_line, last_line in _logical_lines(lines=lines):
        if is_signature(line):
            break
        for i in range(first_line - 1, last_line):
            if is_comment(lines[i]):
                if lineno is None and uncomment_lines([lines[i]])[0].strip():
                    lineno = i + 1
                endlineno = i + 1
                docstring_lines.append(lines[i])

    docstring_value = "\n".join(uncomment_lines(docstring_lines))

    return Docstring(
        value=docstring_value,
        lineno=lineno,
        endlineno=endlineno,
        parent=parent,
    )


def is_end(line: str, *, procedure_type: str) -> bool:
    """
    Check for a matching procedure terminator, allowing indentation and a comment.

    Args:
        line: Logical VBA statement to check.
        procedure_type: Sub, Function, Property Get, or Property Let.

    Returns:
        Whether the statement ends the given procedure type.
    """
    terminator = procedure_type.split()[0]
    return (
        re.fullmatch(
            rf"End[ \t]+{terminator}[ \t]*(?:'.*)?", line.strip(), re.IGNORECASE
        )
        is not None
    )


def parse_args(args: str) -> Generator[VbaArgumentInfo, None, None]:
    """
    Parse the arguments portion of a signature line of a VBA procedure.
    """
    args = args.strip()
    if not len(args):
        return

    for arg in args.split(","):
        yield parse_arg(arg)


def parse_arg(arg: str) -> VbaArgumentInfo:
    arg = arg.strip()
    if not len(arg):
        raise NotImplementedError(
            "What do we do with empty arguments in a function signature?"
        )

    match = re_arg.fullmatch(arg)

    if match is None:
        raise RuntimeError(f"Failed to parse argument: {arg}")
    groups = match.groupdict()

    return VbaArgumentInfo(
        optional=bool(groups["optional"]),
        modifier=groups["modifier"],
        name=groups["name"],
        arg_type=groups["type"],
        default=groups["default"],
    )


def parse_signature(line: str) -> VbaSignatureInfo:
    """
    Parse the signature line of a VBA procedure.
    """
    line = re.sub(r"'.*$", "", line).strip()  # Strip comment and whitespace.

    match = re_signature.fullmatch(line)

    if match is None:
        raise RuntimeError(f"Failed to parse signature: {line}")
    groups = match.groupdict()

    return VbaSignatureInfo(
        visibility=groups["visibility"],
        return_type=groups["returnType"],
        procedure_type=groups["type"],
        name=groups["name"],
        args=list(parse_args(groups["args"] or "")),
    )


def find_procedures(
    code: str, *, parent: Optional[Module] = None
) -> Generator[VbaProcedureInfo, None, None]:
    """
    Collect VBA procedures with parameter-aware Google docstrings.

    Args:
        code: Original VBA source, including any continuation lines.
        parent: Griffe module providing the source path, when collecting a file.

    Yields:
        Procedures with their original signatures, source, and docstrings.
    """
    lines = code.splitlines()

    procedure: Tuple[VbaSignatureInfo, int, int] | None = None
    """
    The signature and its first and last physical line numbers,
    or None when scanning for the start of the next procedure.
    """

    for line, logical_first_line, logical_last_line in _logical_lines(lines=lines):
        if procedure is None:
            # Looking for signature. Ignore everything until we find one.
            if not is_signature(line):
                continue

            procedure = parse_signature(line), logical_first_line, logical_last_line
            continue

        if is_end(line, procedure_type=procedure[0].procedure_type):
            # Found the end of a procedure.
            signature, first_line, signature_last_line = procedure
            last_line = logical_last_line

            # The docstring consists of the comment lines directly after the signature.
            docstring_lines = []
            procedure_source = lines[first_line - 1 : last_line]
            for source_line in lines[signature_last_line : last_line - 1]:
                if not is_comment(source_line):
                    break
                docstring_lines.append(source_line)

            docstring_text_lines = uncomment_lines(docstring_lines)
            docstring_value = "\n".join(docstring_text_lines)
            # Griffe strips leading blank docstring lines before computing warning offsets.
            leading_blank_lines = next(
                (i for i, line in enumerate(docstring_text_lines) if line.strip()),
                0,
            )

            # Supply VBA's implicit types only to docstring parsing.
            # Keep the authored signature unchanged for display.
            return_type = signature.return_type
            if return_type is None and signature.procedure_type.casefold() in (
                "function",
                "property get",
            ):
                return_type = "Variant"

            # See https://mkdocstrings.github.io/griffe/guide/users/how-to/parse-docstrings/
            docstring = Docstring(
                value=docstring_value,
                parser=Parser.google,
                parser_options={},
                lineno=signature_last_line + 1 + leading_blank_lines,
                endlineno=signature_last_line + len(docstring_lines),
                parent=Function(
                    name=signature.name,
                    parent=parent,
                    lineno=first_line,
                    endlineno=last_line,
                    parameters=_VbaParameters(
                        *(
                            Parameter(
                                name=arg.name,
                                annotation=arg.arg_type or "Variant",
                                default=arg.default,
                            )
                            for arg in signature.args
                        )
                    ),
                    returns=return_type,
                ),
            )

            # Yield it and start over.
            yield VbaProcedureInfo(
                signature=signature,
                docstring=docstring,
                first_line=first_line,
                last_line=last_line,
                source=procedure_source,
            )
            procedure = None


def collapse_long_lines(code: str) -> str:
    """
    Collapse lines that are split by continuation characters (underscore).

    Examples:
        >>> collapse_long_lines('''hello _
        ... world''')
        'hello world'
        >>> collapse_long_lines('''hello _ world''')
        'hello _ world'
        >>> collapse_long_lines('hello _  \\nworld')
        'hello world'
    """
    return re.sub(r" _\s*?(\r|\n|\r\n)", " ", code)
