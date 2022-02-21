import re
from typing import List, Generator

from griffe.dataclasses import Docstring
from griffe.docstrings import Parser

from mkdocstrings_handlers.vba.regex import re_signature, re_arg
from mkdocstrings_handlers.vba.types import (
    VbaArgumentInfo,
    VbaSignatureInfo,
    VbaProcedureInfo,
)


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
    return re.match(r"^ *'", line, re.IGNORECASE) is not None


def uncomment_lines(lines: List[str]) -> List[str]:
    return [line.replace("'", "", 1) for line in lines]


def find_file_docstring(code: str) -> Docstring:
    """
    Find the file docstring in the given VBA code.
    It's the first block of comment lines before the first signature, if any.
    """
    docstring_lines = []

    for line in code.splitlines():
        if is_signature(line):
            break
        if is_comment(line):
            docstring_lines.append(line)

    docstring_value = "\n".join(uncomment_lines(docstring_lines))

    # FIXME: https://github.com/mkdocstrings/griffe/issues/38
    docstring_value = docstring_value.replace(":", ";")

    return Docstring(
        value=docstring_value,
        parser=Parser.google,
        parser_options={},
    )


def is_end(line: str) -> bool:
    return line.casefold().startswith("end")


def parse_args(args: str) -> Generator[VbaArgumentInfo, None, None]:
    """
    Parse the arguments portion of a signature line of a VBA procedure.
    """
    for arg in args.split(","):
        arg = arg.strip()
        if not len(arg):
            continue

        match = re_arg.fullmatch(arg)

        if match is None:
            raise RuntimeError(f"Failed to parse argument: {arg}")
        match = match.groupdict()

        yield VbaArgumentInfo(
            optional=bool(match["optional"]),
            modifier=match["modifier"],
            name=match["name"],
            arg_type=match["type"],
            default=match["default"],
        )


def parse_signature(line: str) -> VbaSignatureInfo:
    """
    Parse the signature line of a VBA procedure.
    """
    line = re.sub(r"'.*$", "", line).strip()  # Strip comment and whitespace.

    match = re_signature.fullmatch(line)

    if match is None:
        raise RuntimeError(f"Failed to parse signature: {line}")
    match = match.groupdict()

    return VbaSignatureInfo(
        visibility=match["visibility"],
        return_type=match["returnType"],
        procedure_type=match["type"],
        name=match["name"],
        args=list(parse_args(match["args"] or "")),
    )


def find_procedures(code: str) -> Generator[VbaProcedureInfo, None, None]:
    lines = code.splitlines()
    procedure = None

    for i, line in enumerate(lines):
        if procedure is None:
            # Looking for signature. Ignore everything until we find one.
            if not is_signature(line):
                continue

            procedure = {
                "signature": parse_signature(line),
                "first_line": i + 1,
            }
            continue

        if is_end(line):
            # Found the end of a procedure.
            procedure["last_line"] = i + 1

            # The docstring consists of the comment lines directly after the signature.
            docstring_lines = []
            procedure_source = lines[
                procedure["first_line"] - 1 : procedure["last_line"] - 1
            ]
            for source_line in procedure_source[1:]:
                if not is_comment(source_line):
                    break
                docstring_lines.append(source_line)

            docstring_value = "\n".join(uncomment_lines(docstring_lines))

            # FIXME: https://github.com/mkdocstrings/griffe/issues/38
            docstring_value = docstring_value.replace(":", ";")

            # Yield it and start over.
            yield VbaProcedureInfo(
                signature=procedure["signature"],
                docstring=Docstring(
                    value=docstring_value,
                    parser=Parser.google,
                    parser_options={},
                ),
                first_line=procedure["first_line"],
                last_line=procedure["last_line"],
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
