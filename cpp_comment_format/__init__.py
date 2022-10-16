import argparse
import re
import sys

from ._version import version


def find_matching(
    text: str,
    opening: str,
    closing: str,
    ignore_escaped: bool = True,
) -> dict:
    r"""
    Find matching 'brackets'.

    :param text: The string to consider.
    :param opening: The opening bracket (e.g. "(", "[", "{").
    :param closing: The closing bracket (e.g. ")", "]", "}").
    :param ignore_escaped: Ignore escaped bracket (e.g. "\(", "\[", "\{", "\)", "\]", "\}").
    :return: Dictionary with ``{index_opening: index_closing}``
    """

    a = []
    b = []

    o = re.escape(opening)
    c = re.escape(closing)

    if ignore_escaped:
        o = r"(?<!\\)" + o
        c = r"(?<!\\)" + c

    for i in re.finditer(o, text):
        a.append(i.span()[0])

    for i in re.finditer(c, text):
        b.append(-1 * i.span()[0])

    if len(a) == 0 and len(b) == 0:
        return {}

    if len(a) != len(b):
        raise OSError(f"Unmatching {opening}...{closing} found")

    brackets = sorted(a + b, key=lambda i: abs(i))

    ret = {}
    stack = []

    for i in brackets:
        if i >= 0:
            stack.append(i)
        else:
            if len(stack) == 0:
                raise IndexError(f"No closing {closing} at: {i:d}")
            j = stack.pop()
            ret[j] = -1 * i

    if len(stack) > 0:
        raise IndexError(f"No opening {opening} at {stack.pop():d}")

    return ret


def format_javadoc(text: str) -> str:

    brackets = find_matching(text, "/**", "*/")
    starting = sorted(list(brackets.keys()))
    newline = [i for i, c in enumerate(text) if c == "\n"]
    ret = text.split("\n")

    inewline = 0

    for i in starting:
        while i > newline[inewline]:
            inewline += 1
        s = inewline
        while brackets[i] > newline[inewline]:
            inewline += 1
        inewline += 1
        e = inewline

        block = ret[s:e]
        indent = len(block[0].split("/**")[0])
        for j in range(1, len(block) - 1):
            if re.match(r"^\s*$", block[j]):
                block[j] = " " * indent + " *"
            elif not re.match(r"^\s*\*", block[j]) or re.match(r"^\s*\*\*\w*.*", block[j]):
                _, ind, c, _ = re.split(r"^(\s*)(.*)$", block[j])
                block[j] = " " * indent + " * " + " " * (len(ind) - indent) + c
            for key in ["param", "tparam", "return", "warning", "brief", "throws", "file"]:
                block[j] = re.sub(rf"^(\s*)(\*\s*)(\\{key})(.*)$", rf"\1\2@{key}\4", block[j])
        block[-1] = " " * indent + " */"
        ret[s:e] = block

    return "\n".join(ret)


def _format_parser():
    """
    Return parser for :py:func:`format`.
    """

    desc = """
    Restrict version of packages based on another YAML file. Example::

        conda_envfile_restrict env1.yml env2.yml > env3.yml

    To check conda-forge recipes, use::

        conda_envfile_restrict --conda meta.yml env2.yml

    In this case, this function only checks and outputs a ``1`` return code if the conda file
    is not restrictive enough.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-i", "--in-place", action="store_true", help="Apply formatting in place.")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("file", type=str, nargs="*", help="Input file(s).")
    return parser


def format(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _format_parser()
    args = parser.parse_args(args)

    for file in args.file:
        with open(file) as f:
            inp = f.read()
            ret = format_javadoc(inp)
            if args.in_place and inp != ret:
                with open(file, "w") as f:
                    f.write(ret)
            else:
                print(ret)


def _cli():
    return format(sys.argv[1:])
