#!/usr/bin/env python

import argparse
import re
import string
from itertools import chain, takewhile
from pathlib import Path

from pyparsing import (Char, Group, Literal, OneOrMore, Word, ZeroOrMore,
                       alphanums)


def parse_common_block(s: str) -> list:
    """Parse a common block."""
    myword = Word(alphanums + "_")
    inside = OneOrMore(myword + ZeroOrMore(","))
    parenthesis = ZeroOrMore(Char("(") + inside + Char(")"))
    parser = Literal("common") + Char('/') + myword + Char('/') + \
        OneOrMore(Group(myword + parenthesis + ZeroOrMore(Char(","))))

    return parser.parseString(s).asList()


def search_for_procedures(index: int, xs: str, procedure: str = "subroutine") -> tuple:
    """Search for string slice containing the procedure."""
    start = re.search(f"      {procedure}", xs[index:])
    if start is not None:
        end = re.search("      end\n", xs[index + start.start():])
        return index + start.start(), index + start.start() + end.end()
    else:
        return None


class Expression:
    """Naive representation of an expression."""

    def __init__(self, s: str, kind: str):
        self.text = s
        self.kind = kind


class Refactor:
    """Object to remove common block from a project."""

    def __init__(self, name: str, path: Path):
        """Initialize Refactor class."""
        self.block_name = name
        self.path = path
        self.keyword = f"common /{name}/.*"

    def has_common_block(self, path: Path) -> bool:
        """Look up for a specific common block in a given file."""
        with open(path, 'r') as f:
            xs = f.read()

        result = re.search(self.keyword, xs)
        return True if result is not None else False

    def generate_new_module(self, variables: list, variable_names: str) -> str:
        """Generate new module replacing the common block."""
        integer_variables = string.ascii_lowercase[8:14]

        # Sort alphabetically
        variables.sort()

        def add_kind(v: str) -> str:
            if v[0].lower() in integer_variables:
                return "integer  ::"
            else:
                return "real(dp) ::"

        kinds_and_variables = '\n'.join(
            f"    {add_kind(v)} {v}" for v in variables)

        new = f"""
module {self.block_name}
    !> Arguments: {variable_names}
    use precision_kinds, only: dp
    include 'vmc.h'

{kinds_and_variables}

    save
end module {self.block_name}
"""
        return new

    def get_target_files(self) -> tuple:
        """Get the target files to replace."""
        fortran_files = get_src_files(self.path, 'vmc')
        includes = get_src_files(self.path, 'include')
        target_source = list(
            filter(lambda x: self.has_common_block(x), fortran_files))
        target_include = list(
            filter(lambda x: self.has_common_block(x), includes))

        return target_source, target_include

    def read_common_block_definition(self, path: Path) -> str:
        """Read the definition of the common block."""
        with open(path, 'r') as f:
            xs = f.read()

        # Get common block definition
        result = re.search(self.keyword, xs)

        # Continuation line
        next_lines = result.string[result.end():].split()

        # Search for continuation lines
        new_line_index = result.end() + 6
        start_common_block = result.group(0).strip()

        # Search for first char in the newt line
        if next_lines[0][0] != '&':
            self.multiline = False
            common_block = start_common_block
        else:
            self.multiline = True
            common_block = start_common_block + \
                search_for_line_continuation(result.string[new_line_index:])

        return split_common_block(common_block)

    def generate_module_call(self, definition: str) -> str:
        """Generate the call to the new module and variable names."""
        # remove parenthesis
        variables = ', '.join(x.split('(')[0] for x in definition)
        statement = f"use {self.block_name}, only: {variables}\n"

        return statement, variables

    def split_into_procedures(self, path: Path, procedure: str = "subroutine"):
        """Split file into subroutines and/or functions."""
        with open(path, 'r') as f:
            xs = f.read()

        index = 0
        size = len(xs)
        components = []
        while True:
            rs = search_for_procedures(index, xs, procedure)
            # There are not more procedures
            if rs is None:
                components.append(Expression(xs[index:size], "other"))
                break
            else:
                start, end = rs
                # Add comments and other things in the middle
                components.append(Expression(xs[index: start], "other"))
                # Add the procedure
                components.append(Expression(xs[start:end], procedure))
                index = end

        return components

    def change_subroutine(self, module_call: str, xs: str) -> str:
        """Replace common block in subroutine."""
        # Search and removed implicit
        before_implicit, after_implicit = split_str_at_keyword(
            "implicit real.*", xs)
        # search and removed common block
        before_common, after_common = split_str_at_keyword(
            self.keyword, after_implicit)

        new_subroutine = before_implicit + module_call + \
            "      implicit real*8(a-h,o-z)\n" + before_common + after_common

        return new_subroutine

    def replace_common_blocks(self, module_call: str, files: list):
        """Replace the common block for the subroutines in the file."""
        def conditional_replacement(x: Expression) -> str:
            predicate_1 = x.kind != "other"
            predicate_2 = f"/{self.block_name}/" in x.text
            if predicate_1 and predicate_2:
                return self.change_subroutine(module_call, x.text)
            else:
                return x.text

        for path in files:
            print("Changing file: ", path)
            new_subroutines = ''.join(conditional_replacement(
                x) for x in self.split_into_procedures(path))
            with open(path, 'r+') as f:
                f.write(new_subroutines)

    def add_new_module(self, new_module: str):
        """Add new module replacing the common block."""
        with open(self.path / "src/vmc/m_common.f90", 'a') as f:
            f.write(new_module)

    def refactor(self):
        """Remove common block."""
        target_source, target_include = self.get_target_files()
        if target_include:
            print("Shit happens! There are common blocks in the include files")
        elif not target_source:
            print(
                f"There is not {self.block_name} common block in the source files")
        else:
            definition = self.read_common_block_definition(target_source[0])
            module_call, variables = self.generate_module_call(definition)
            new_module = self.generate_new_module(definition, variables)
            self.replace_common_blocks(module_call, target_source)
            self.add_new_module(new_module)


def split_str_at_keyword(keyword: str, lines: str) -> str:
    """Split lines at `keyword` returning the lines before and after keyword."""
    result = re.search(keyword, lines)
    sub = result.string
    return sub[:result.start()], sub[result.end():]


def split_common_block(s: str) -> list:
    """Split common block into its individual variables."""
    xs = parse_common_block(s)
    # remove initial kewords
    lists = xs[4:]

    # comma separate variables
    variables = [''.join(x) for x in lists]

    # remove commas
    return [x if x[-1] != ',' else x[:-1] for x in variables]


def search_for_line_continuation(s: str) -> str:
    """Search for & line continuations."""
    xs = takewhile(lambda x: x.startswith("&"), s.split())

    # Remove the & symbol
    return ''.join([x[1:] for x in xs])


def get_src_files(path: Path, folder: str):
    """List of the fortran 77 source files."""
    vmc_path = path / f"src/{folder}"
    return chain(vmc_path.glob("*.f"), vmc_path.glob("*.h"))


def main():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        description="refactor -n <common block name> -p folder_path")
    # configure logger
    parser.add_argument('-n', required=True,
                        help="Common block name")
    parser.add_argument('-p', help="path to champ", default=".")
    args = parser.parse_args()

    rs = Refactor(args.n, Path(args.p))
    rs.refactor()


if __name__ == "__main__":
    main()
