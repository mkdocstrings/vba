from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from griffe.dataclasses import Docstring


@dataclass
class VbaArgumentInfo:

    name: str

    optional: bool

    modifier: Optional[str]

    arg_type: Optional[str]

    default: Optional[str]

    def render(self):
        parts = []
        if self.optional:
            parts.append(self.optional)
        if self.modifier:
            parts.append(self.modifier)
        parts.append(self.name)
        if self.arg_type:
            parts.append(f"As {self.arg_type}")
        if self.default:
            parts.append(f"= {self.default}")
        return " ".join(parts)


@dataclass
class VbaSignatureInfo:
    visibility: str
    return_type: str
    procedure_type: str
    name: str
    args: List[VbaArgumentInfo]


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
        return self.path.as_posix()
