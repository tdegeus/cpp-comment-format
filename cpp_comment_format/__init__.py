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


def _comment_blocks(text: str, opening: str = "/**", closing: str = "*/") -> dict:
    """
    Find comment blocks in text.

    :param text: The string to consider.
    :param opening: The opening symbol (e.g. "/**").
    :param closing: The closing symbol (e.g. "*/").
    :return: Dictionary with ``{line_start: line_end}``
    """

    brackets = find_matching(text, opening, closing)
    opening_chars = sorted(list(brackets.keys()))
    newline = [i for i, c in enumerate(text) if c == "\n"]

    ret = {}
    inewline = 0

    for opening_char in opening_chars:
        while opening_char > newline[inewline]:
            inewline += 1
        start_line = inewline
        while brackets[opening_char] > newline[inewline]:
            inewline += 1
        inewline += 1
        end_line = inewline
        ret[start_line] = end_line

    return ret


class _FormatLineDoxygen:
    def __init__(self, prefix: str):

        replace = ["\\", "@"]
        replace.remove(prefix)
        self.replace = [re.escape(i) for i in replace]
        self.prefix = re.escape(prefix)

    def format_line_javadoc(self, line):

        ret = line

        for symbol in self.replace:
            for key in ["param", "tparam", "return", "warning", "brief", "throws", "file"]:
                ret = re.sub(
                    rf"^(\s*)(\*\s*)({symbol}{key})(.*)$",
                    rf"\1\2{self.prefix}{key}\4",
                    ret,
                )

        return ret


def _format_javadoc_doxygen(text: str, doxygen_prefix: str) -> str:
    """
    Format docstrings according to javadoc/doxygen conventions::

        /**
         * This is a docstring.
         *
         * @param a This is a parameter.
         */
    """

    doxygen = _FormatLineDoxygen(doxygen_prefix)

    comment_blocks = _comment_blocks(text, "/**", "*/")
    ret = text.splitlines()

    for start_line, end_line in comment_blocks.items():

        block = ret[start_line:end_line]
        indent = len(block[0].split("/**")[0])
        block[-1] = " " * indent + " */"

        for i in range(1, len(block) - 1):

            if re.match(r"^\s*$", block[i]):
                block[i] = " " * indent + " *"
            elif not re.match(r"^\s*\*", block[i]) or re.match(r"^\s*\*\*\w*.*", block[i]):
                _, ind, cmd, _ = re.split(r"^(\s*)(.*)$", block[i])
                block[i] = " " * indent + " * " + " " * (len(ind) - indent) + cmd

            block[i] = doxygen.format_line_javadoc(block[i])

        ret[start_line:end_line] = block

    return "\n".join(ret)


def format(text: str, style: str = "javadoc", doxygen: str = "@") -> str:
    r"""
    Change formatting of comment blocks. See `doxygen <https://doxygen.nl/manual/docblocks.html>`_.

    :param style: Select style: ``"javadoc"``.
    :param doxygen: Format doxygen commands with certain prefix (``"@", "\"``). False to skip.
    :return: Formatted text.
    """

    if style == "javadoc" and doxygen:
        return _format_javadoc_doxygen(text, doxygen_prefix=doxygen)

    raise ValueError(f"Unknown style: '{style}'")


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
    parser.add_argument("-s", "--style", default="javadoc", help="Select style: 'javadoc'.")
    parser.add_argument(
        "-d",
        "--doxygen",
        default="@",
        help="Format doxygen commands with certain prefix ('@', '\\'). False to skip.",
    )
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("file", type=str, nargs="*", help="Input file(s).")
    return parser


def cli_format(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _format_parser()
    args = parser.parse_args(args)

    for file in args.file:
        with open(file) as f:
            inp = f.read()
            ret = format(inp, style=args.style, doxygen=args.doxygen)
            if args.in_place and inp != ret:
                with open(file, "w") as f:
                    f.write(ret)
            else:
                print(ret)


def _cli():
    return cli_format(sys.argv[1:])
