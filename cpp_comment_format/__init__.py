import argparse
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap

import yaml

from ._version import version


def find_matching(
    text: str,
    opening: str,
    closing: str,
    escape_input: bool = True,
    ignore_escaped: bool = True,
) -> dict:
    r"""
    Find matching 'brackets'.
    Note that dangling closing 'brackets' are ignored.
    For this module this has the specific advantage that e.g. ``/* ... */`` inside code blocks
    is ignored if ``/** ... */`` is searched.

    :param text: The string to consider.
    :param opening: The opening bracket (e.g. ``"("``, ``"["``, ``"{"``).
    :param closing: The closing bracket (e.g. ``")"``, ``"]"``, ``"}"``).
    :param escape_input: If ``True``, escape the input string (e.g. ``"\"`` becomes ``"\\\"``).
    :param ignore_escaped: Ignore escaped bracket (e.g. ``"\("``, ``"\)"``, etc).
    :return: Dictionary with ``{index_opening: index_closing}``
    """

    a = []
    b = []

    if escape_input:
        o = re.escape(opening)
        c = re.escape(closing)
    else:
        o = opening
        c = closing

    if ignore_escaped:
        o = r"(?<!\\)" + o
        c = r"(?<!\\)" + c

    for i in re.finditer(o, text):
        a.append(i.span()[0])

    for i in re.finditer(c, text):
        b.append(-1 * i.span()[0])

    if len(a) == 0 and len(b) == 0:
        return {}

    brackets = sorted(a + b, key=lambda i: abs(i))

    ret = {}
    stack = []

    for i in brackets:
        if i >= 0:
            stack.append(i)
        else:
            if len(stack) == 0:
                continue
            j = stack.pop()
            ret[j] = -1 * i

    if len(stack) > 0:
        raise IndexError(f"No opening {opening} at {stack.pop():d}")

    return ret


def _comment_blocks(text: str, opening: str, closing: str, escape_input: bool) -> dict:
    """
    Find comment blocks in text.

    :param text: The string to consider.
    :param opening: The opening symbol (e.g. ``"/**"``).
    :param closing: The closing symbol (e.g. "*/").
    :param escape_input: If ``True``, escape the input string (e.g. ``"\"`` becomes ``"\\\"``).
    :return: Dictionary with ``{line_start: line_end}``
    """

    brackets = find_matching(text, opening, closing, escape_input=escape_input)
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
    """
    Support class to format doxygen commands.

    :param prefix: The prefix to use (e.g. "@").
    """

    def __init__(self, prefix: str):
        replace = ["\\", "@"]
        replace.remove(prefix)
        self.replace = [re.escape(i) for i in replace]
        self.prefix = re.escape(prefix)

    def format_line_javadoc(self, line):
        """
        Format a line of comment.

        :param line: Comment line.
        :return: Formatted input.
        """

        ret = line

        for symbol in self.replace:
            for key in [
                "author",
                "brief",
                "code",
                "copydoc",
                "copydoc",
                "copyright",
                "endcode",
                "file",
                "note",
                "param",
                "return",
                "throws",
                "tparam",
                "warning",
            ]:
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
    docstrings = Docstrings(text)

    for iblock, doc in enumerate(docstrings):
        block = doc.split("\n")
        indent = len(block[0].split("/**")[0])
        block[-1] = " " * indent + " */"

        for i in range(1, len(block) - 1):
            if re.match(r"^\s*$", block[i]):
                block[i] = " " * indent + " *"
            elif not re.match(r"^\s*\*", block[i]) or re.match(r"^\s*\*\*\w*.*", block[i]):
                _, ind, cmd, _ = re.split(r"^(\s*)(.*)$", block[i])
                block[i] = " " * indent + " * " + " " * (len(ind) - indent) + cmd
            elif re.match(r"^\s*\*.*", block[i]):
                _, ind, _, cmd, _ = re.split(r"^(\s*)(\*)(.*)$", block[i])
                block[i] = " " * indent + " *" + cmd

            block[i] = doxygen.format_line_javadoc(block[i])

        docstrings[iblock] = "\n".join(block)

    return str(docstrings)


def _format_javadoc_internal_indent(text: str, tabsize: int = None) -> str:
    """
    Fix indentation of indented code inside javadoc comment blocks, that are formatted::

        /**
         * This is a docstring.
         *
         *      This is indented code.
         */

    This function makes sure that the indentation of the indented code matched the global tab size.

    :param text: Source code.
    :param tabsize: The global tab size (default: extract automatically).
    :return: Source code with fixed indentation.
    """

    docstrings = Docstrings(text)

    if tabsize is None:
        indent = []
        for doc in docstrings:
            indent.append(len(doc.split("/**")[0]))
        indent = list(filter(lambda i: i != 0, indent))
        tabsize = round(sum(indent) / len(indent))

    for iblock, doc in enumerate(docstrings):
        block = doc.split("\n")

        for i in range(1, len(block) - 1):
            if re.match(r"^(\s*)(\*)(\s\s+)(.*)", block[i]):
                _, ind, sym, space, rest, _ = re.split(r"^(\s*)(\*)(\s\s+)(.*)", block[i])
                ex = (len(ind) + len(sym) + len(space)) % tabsize
                if ex:
                    block[i] = ind + sym + space + " " * (tabsize - ex) + rest

        docstrings[iblock] = "\n".join(block)

    return str(docstrings)


class Docstrings:
    """
    Class to format docstrings.
    From this class, one can loop over all docstrings in a file and format them. E.g.::

        docstrings = Docstrings(code)

        for i, doc in enumerate(docstrings):
            doc = ...
            docstrings[i] = doc

        formatted_code = str(docstrings)

    :param text: The source code.
    :param opening: The opening symbol of the docstring (e.g. ``"/**"``).
    :param closing: The closing symbol of the docstring (e.g. ``"/*"``).
    :param escape_input: If ``True``, escape the input string (e.g. ``"\"`` becomes ``"\\\"``).
    """

    def __init__(
        self,
        text: str,
        opening: str = "/\\*\\*\\s*\n",
        closing: str = r"\*/",
        escape_input: bool = False,
    ):
        newline = [i.span()[0] for i in re.finditer(r"\n", text)]
        doc_blocks = _comment_blocks(text, opening, closing, escape_input=escape_input)

        if len(doc_blocks) == 0:
            self.blocks = [text]
            self.comment = [False]
            return

        code_blocks = {}
        last = 0
        for start_line, end_line in doc_blocks.items():
            code_blocks[last] = start_line - 1
            last = end_line
        code_blocks[last] = -1

        scode = min(code_blocks)
        ecode = code_blocks[scode]

        if min(doc_blocks) == 0:
            self.blocks = []
            self.comment = []
        elif min(code_blocks) == 0:
            self.blocks = [text[: newline[ecode]]]  # noqa: E203
            self.comment = [False]
        else:
            self.blocks = [text[newline[scode - 1] + 1 : newline[ecode]]]  # noqa: E203
            self.comment = [False]

        while True:
            sdoc = ecode + 1
            edoc = doc_blocks[sdoc]

            scode = edoc
            ecode = code_blocks[scode]

            if sdoc == 0:
                self.blocks.append(text[: newline[edoc - 1]])  # noqa: E203
            else:
                self.blocks.append(text[newline[sdoc - 1] + 1 : newline[edoc - 1]])  # noqa: E203
            self.comment.append(True)

            if ecode == -1:
                self.blocks.append(text[newline[scode - 1] + 1 :])  # noqa: E203
                self.comment.append(False)
                break

            self.blocks.append(text[newline[scode - 1] + 1 : newline[ecode]])  # noqa: E203
            self.comment.append(False)

        self.index = {}
        i = 0
        for j in range(len(self.blocks)):
            if self.comment[j]:
                self.index[i] = j
                i += 1

    def __iter__(self):
        for i in range(len(self.blocks)):
            if self.comment[i]:
                yield self.blocks[i]

    def __setitem__(self, i, value):
        self.blocks[self.index[i]] = value

    def __getitem__(self, i):
        return self.blocks[self.index[i]]

    def __str__(self):
        return "\n".join(self.blocks)


def change_quotes(text: str, search: str, replace: str, ignore_escaped: bool = True) -> str:
    r"""
    Change quotes used to quote text in all comment blocks. For example::

        "This is ``a`` variable."  ->  "This is `a` variable."

    :param text: Source code.
    :param search: The quote to search for, e.g. ``'``.
    :param replace: The quote to replace with, e.g. ``'``.
    :param ignore_escaped: Ignore escaped quotes (escaped with \\).
    :return: Source code with changed formatting.
    """

    search = re.escape(search)
    replace = re.escape(replace)

    if ignore_escaped:
        search = r"(?<!\\)" + search

    docstrings = Docstrings(text)

    for i, doc in enumerate(docstrings):
        docstrings[i] = re.sub(
            rf"({search})([^{search}]*)({search})", rf"{replace}\2{replace}", doc
        )

    return str(docstrings)


def format(
    text: str,
    style: str = "javadoc",
    doxygen: str = "@",
    tabsize: int = None,
    align_codeblock: bool = False,
) -> str:
    r"""
    Change formatting of comment blocks. See `doxygen <https://doxygen.nl/manual/docblocks.html>`_.

    :param style: Select style: ``"javadoc"``.
    :param doxygen: Format doxygen commands with certain prefix (``"@", "\"``). False to skip.
    :param tabsize: Specify tabsize.
    :param align_codeblock: Align code blocks inside the comment blocks.
    :return: Formatted text.
    """

    if style == "javadoc" and doxygen:
        ret = _format_javadoc_doxygen(text, doxygen_prefix=doxygen)
    else:
        raise ValueError(f"Unknown style: '{style}'")

    if align_codeblock:
        ret = _format_javadoc_internal_indent(ret, tabsize=tabsize)

    return ret


def _search_upwards_for_file(filename: str) -> pathlib.Path:
    """
    Search in the current directory and all directories above it for a file of a particular name.
    From: https://stackoverflow.com/a/68994012/2646505

    :param filename: The filename to look for.
    :return: The location of the first file found (``None`` if none was found).
    """
    d = pathlib.Path.cwd()
    root = pathlib.Path(d.root)

    while d != root:
        attempt = d / filename
        if attempt.exists():
            return attempt
        d = d.parent

    return None


def clang_format(
    text: str,
    executable: str = "clang-format",
    style: dict = None,
) -> str:
    r"""
    Format code blocks using clang-format.

    :note:
        The assumption is made that if any code block is formatted::
            @code{.cpp}
            ...
            @endcode
        (i.e. the ``@code`` and ``@endcode`` are on separate lines).

    :param text: Source code.
    :param blocks: List of code blocks.
    :param executable: Path to clang-format executable.
    :return: Source code with formatted code blocks.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tempdir = pathlib.Path(tmpdir)
        sourcefile = tempdir / "source.cpp"

        docstrings = Docstrings(text)

        if style is not None:
            with open(tempdir / ".clang-format", "w") as file:
                yaml.dump(style, file)

        for idoc, doc in enumerate(docstrings):
            # line number of each character
            lineno = [0 for _ in range(len(doc))]
            i = 0
            line = 0
            for line, match in enumerate(re.finditer(r"\n", doc)):
                lineno[i : match.span()[0]] = [line for _ in range(match.span()[0] - i)]
                i = match.span()[0]
                lineno[i] = line
                i += 1
            lineno[i:] = [line + 1 for _ in range(len(doc) - i)]

            matching = find_matching(
                doc, r"([\@\\])(code{\.cpp})", r"([\@\\])(endcode)", escape_input=False
            )

            ret = []
            doclines = doc.splitlines()
            prev = 0

            for opening, closing in matching.items():
                ret += doclines[prev : lineno[opening]]
                prev = lineno[closing] + 1

                target = doclines[lineno[opening] : lineno[closing] + 1]
                indent = os.path.commonprefix(target)
                if indent[-1] != " ":
                    indent += " "
                target = [line.lstrip(indent) for line in target]
                source = target[1:-1]
                sourcefile.write_text("\n".join(source))
                subprocess.run([executable, "-i", str(sourcefile)])
                source = sourcefile.read_text()
                target = [target[0], source, target[-1]]
                ret += [textwrap.indent("\n".join(target), indent)]

            ret += doclines[prev:]
            docstrings[idoc] = "\n".join(ret)

    return str(docstrings)


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
    parser.add_argument("-t", "--tabsize", type=int, help="Specify tabsize.")
    parser.add_argument(
        "--change-quote", nargs=2, action="append", default=[], help="Change quote: SEARCH REPLACE."
    )
    parser.add_argument(
        "-c",
        "--code-block",
        action="store_true",
        help="Align code-block in comment blocks with tabsize.",
    )
    parser.add_argument(
        "-d",
        "--doxygen",
        type=str,
        default="@",
        help="Format doxygen commands with certain prefix ('@', '\\'). False to skip.",
    )
    parser.add_argument(
        "--clang-format",
        action="store_true",
        help=r"Apply clang-format to blocks between @code{.cpp} and @endcode.",
    )
    parser.add_argument(
        "--clang-format-executable",
        type=str,
        default="clang-format",
        help="Specify clang-format executable.",
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
            ret = format(
                inp,
                style=args.style,
                doxygen=args.doxygen,
                tabsize=args.tabsize,
                align_codeblock=args.code_block,
            )
            if args.change_quote:
                for search, replace in args.change_quote:
                    ret = change_quotes(ret, search, replace)
            if args.clang_format:
                style = _search_upwards_for_file(".clang-format")
                if style is not None:
                    style = yaml.load(style.read_text(), Loader=yaml.FullLoader)
                ret = clang_format(ret, args.clang_format_executable, style)
            if args.in_place and inp != ret:
                with open(file, "w") as f:
                    f.write(ret)
            elif not args.in_place:
                print(ret)


def _cli():
    return cli_format(sys.argv[1:])
