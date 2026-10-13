from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from griffe import Docstring


@dataclass
class VbaArgumentInfo:
    name: str

    optional: bool

    modifier: Optional[str]

    arg_type: Optional[str]

    default: Optional[str]

    array: bool = False
    """
    Whether the argument name has an authored array suffix.
    """

    def render(self) -> str:
        """
        Render the authored argument type, modifiers, array suffix, and default.

        Returns:
            The VBA argument declaration.
        """
        parts = []
        if self.optional:
            parts.append("Optional")
        if self.modifier:
            parts.append(self.modifier)
        parts.append(self.name + ("()" if self.array else ""))
        if self.arg_type:
            parts.append(f"As {self.arg_type}")
        if self.default:
            parts.append(f"= {self.default}")
        return " ".join(parts)


@dataclass
class VbaSignatureInfo:
    visibility: Optional[str]
    return_type: Optional[str]
    procedure_type: str
    name: str
    args: List[VbaArgumentInfo]

    def render(self, *, show_arguments: bool, line_length: Optional[int]) -> str:
        """
        Render a complete declaration or a heading without its signature.

        Args:
            show_arguments: Include parameters and an explicitly authored return type.
            line_length: Wrap long declarations at this width, or None to keep one line.

        Returns:
            The declaration, with VBA continuation markers when wrapped.
        """
        heading = " ".join(
            part for part in (self.visibility, self.procedure_type, self.name) if part
        )
        if not show_arguments:
            return heading
        arguments = [argument.render() for argument in self.args]
        returns = f" As {self.return_type}" if self.return_type else ""
        signature = heading + "(" + ", ".join(arguments) + ")" + returns
        if line_length is not None and len(signature) > line_length:
            wrapped = heading + "()"
            if arguments:
                wrapped = (
                    heading
                    + "( _\n"
                    + ", _\n".join("    " + argument for argument in arguments)
                    + ")"
                )
            if returns and len(wrapped.rsplit("\n", 1)[-1] + returns) > line_length:
                return wrapped + " _\n    " + returns.lstrip()
            return wrapped + returns
        return signature


@dataclass
class VbaProcedureInfo:
    signature: VbaSignatureInfo

    docstring: Optional[Docstring]

    first_line: int
    """
    1-indexed
    """

    last_line: int
    """
    1-indexed
    """

    source: List[str]

    def argument_modifiers(self, *, name: str) -> str:
        """
        Find authored argument modifiers using VBA's name matching rules.

        Args:
            name: Parameter spelling used in the documentation.

        Returns:
            The authored Optional/ByVal/ByRef/ParamArray modifiers, or an empty string.
        """
        for argument in self.signature.args:
            if argument.name.casefold() == name.lstrip("*").casefold():
                return " ".join(
                    part
                    for part in (
                        "Optional" if argument.optional else "",
                        argument.modifier,
                    )
                    if part
                )
        return ""

    @property
    def has_docstrings(self) -> bool:
        return self.docstring is not None


@dataclass
class VbaModuleInfo:
    docstring: Optional[Docstring]

    source: List[str]

    path: Path

    procedures: List[VbaProcedureInfo]

    @property
    def has_docstrings(self) -> bool:
        return self.docstring is not None or any(
            p.has_docstrings for p in self.procedures
        )

    @property
    def name(self) -> str:
        """
        Return the source filename for headings that omit the full path.

        Returns:
            The source filename, including its extension.
        """
        return self.path.name
