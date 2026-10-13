import re

type_name = r"[A-Z_][A-Z0-9_]*(?:\.[A-Z_][A-Z0-9_]*)*"

re_arg = re.compile(
    r"((?P<optional>Optional) +)?"
    r"((?P<modifier>ByVal|ByRef|ParamArray) +)?"
    r"(?P<name>[A-Z_][A-Z0-9_]*)"
    r"(?P<array>\(\))?"
    rf"( +As +(?P<type>{type_name}))?"
    r"( *= *(?P<default>.*))?",
    re.IGNORECASE,
)

re_signature = re.compile(
    r"((?P<visibility>Private|Public) +)?"
    r"(?P<type>Sub|Function|Property (Let|Get|Set)) *"
    r"(?P<name>[A-Z_][A-Z0-9_]*)\( *(?P<args>.*?) *\)"
    rf"( +As +(?P<returnType>{type_name}(?:\(\))?))?",
    re.IGNORECASE,
)

if __name__ == "__main__":
    print(re_arg.pattern)
    print(re_signature.pattern)
