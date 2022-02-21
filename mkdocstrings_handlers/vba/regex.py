import re

re_arg = re.compile(
    r"((?P<optional>Optional) +)?"
    r"((?P<modifier>ByVal|ByRef) +)?"
    r"(?P<name>[A-Z_][A-Z0-9_]*)"
    r"( +As +(?P<type>[A-Z_][A-Z0-9_]*))?"
    r"( *= *(?P<default>.*))?",
    re.IGNORECASE,
)

re_signature = re.compile(
    r"((?P<visibility>Private|Public) +)?"
    r"(?P<type>Sub|Function|Property (Let|Get)) *"
    r"(?P<name>[A-Z_][A-Z0-9_]*)\( *(?P<args>[A-Z0-9_ ,=]*)\)"
    r"( +As +(?P<returnType>[A-Z_][A-Z0-9_]*))?",
    re.IGNORECASE,
)

if __name__ == "__main__":
    print(re_arg.pattern)
    print(re_signature.pattern)
