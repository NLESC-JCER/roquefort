#!/usr/bin/env python

import argparse
import re
import string
from itertools import chain, takewhile
from pathlib import Path

from pyparsing import (Char, Group, Literal, OneOrMore, Word, ZeroOrMore,
                       alphanums)
from typing import List, Optional


def parse_common_block(s: str) -> list:
    """Parse a common block."""
    myword = Word(alphanums + "_")
    inside = OneOrMore(myword + ZeroOrMore("*") + ZeroOrMore(","))
    parenthesis = ZeroOrMore(Char("(") + inside + Char(")"))
    parser = Literal("common") + Char('/') + myword + Char('/') + \
        OneOrMore(Group(myword + parenthesis + ZeroOrMore(Char(","))))

    return parser.parseString(s).asList()


def search_for_procedures(index: int, xs: str, procedure: str = "subroutine") -> tuple:
    """Search for string slice containing the procedure."""
    start = re.search(f"      {procedure}", xs[index:])
    if start is not None:
        end = re.search(r"(?i)      end\s*\n", xs[index + start.start():])
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
        self.keyword = f"      common /{name}/.*"
        self.multiline = False

    def has_common_block(self, path: Path) -> bool:
        """Look up for a specific common block in a given file."""
        with open(path, 'r') as f:
            xs = f.read()

        result = re.search(self.keyword, xs)
        return True if result is not None else False

    def generate_new_module(self, variables: List[str], variable_names: str) -> str:
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
    private

    public :: {variable_names}
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
        if next_lines and next_lines[0][0] != '&':
            self.multiline = False
            common_block = start_common_block
        else:
            self.multiline = True
            rest = search_for_line_continuation(result.string[new_line_index:])
            common_block = start_common_block + rest

        return split_common_block(common_block)

    def generate_module_call(self, definition: str) -> str:
        """Generate the call to the new module and variable names."""
        # remove parenthesis and sort
        variables = [x.split('(')[0] for x in definition]
        variables.sort()
        str_variables = ", ".join(variables)
        if self.multiline:
            multiline_variable = split_variables_into_multiple_lines(variables)
        else:
            multiline_variable = str_variables
        statement = f"use {self.block_name}, only: {multiline_variable}\n"

        return statement, str_variables

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
        implicits = ["none", "double", "real"]
        while implicits:
            try:
                key = implicits.pop()
                pattern = f"implicit {key}.*"
                before_implicit, after_implicit = split_str_at_keyword(
                    pattern, xs, ignorecase=True)
                break
            except AttributeError:
                pass

        # search and removed common block
        before_common, after_common = split_str_at_keyword(
            self.keyword, after_implicit, multiline=self.multiline)

        new_subroutine = before_implicit + module_call + \
            "      implicit real*8(a-h,o-z)\n" + \
            before_common + after_common[1:]

        return new_subroutine

    def replace_common_blocks(self, module_call: str, files: List[Path], procedure: str):
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
                x) for x in self.split_into_procedures(path, procedure))
            with open(path, 'w') as f:
                f.write(new_subroutines)

    def add_new_module(self, new_module: str):
        """Add new module replacing the common block."""
        with open(self.path / "src/vmc/m_common.f90", 'a') as f:
            f.write(new_module)

    def refactor(self):
        """Remove common block."""
        target_source, target_include = self.get_target_files()
        if target_include:
            self.process_include_common_blocks(target_include)
        elif not target_source:
            print(
                f"There is not {self.block_name} common block in the source files")
        else:
            self.process_source_common_blocks(target_source)

    def process_source_common_blocks(self, target_source: List[Path]) -> None:
        """Replace the common blocks from the source file."""
        definition = self.read_common_block_definition(target_source[0])
        module_call, variables = self.generate_module_call(definition)
        new_module = self.generate_new_module(definition, variables)
        # Add variable to new module
        self.add_new_module(new_module)
        # Replace common blocks in subroutines
        print("REPLACING SUBROUTINES!")
        self.replace_common_blocks(
            module_call, target_source, "subroutine")
        # Replace common blocks in functions
        print("REPLACING FUNCTIONS!")
        self.replace_common_blocks(
            module_call, target_source, "function")

    def process_include_common_blocks(self, target_include: List[Path]) -> None:
        """Process the files that contain include files with commmon blocks."""
        source_folder = "src/vmc"
        definitions = self.read_common_block_definition(target_include[0])
        module_call, variables = self.generate_module_call(definitions)
        used_variables = self.search_for_variables_in_src(
            variables.split(','), source_folder)

        self.remove_common_block_from_include(target_include[0])
        if not used_variables:
            print(
                f"THE VARIABLES DEFINED IN THE COMMON BLOCK {self.block_name} ARE NOT USED IN THE SOURCE CODE!")
        else:
            used_definitions = [x for x in definitions if any(
                name in x for name in used_variables)]
            new_module = self.generate_new_module(
                used_definitions, used_variables)
            print("The following variables need to be replace: ")
            print(used_variables)
            # # Add variable to new module
            # self.add_new_module(new_module)
            # print("REPLACING SUBROUTINES!")
            # print("REPLACING FUNCTIONS!")

    def remove_common_block_from_include(self, file_path: Path) -> None:
        """Remove the common block  that are not use in the source file."""
        # Check what variables are used in the source code
        with open(file_path, 'r') as f:
            lines = f.readlines()
        with open(file_path, 'w') as f:
            for line in lines:
                if not all(x in line for x in (self.block_name, "common")):
                    f.write(line)

    def search_for_variables_in_src(self, definitions: List[str], folder: str) -> Optional[List[str]]:
        """Check what the variables in the common block  are use in the `.f` source files."""
        vmc_path = self.path / folder
        # Search in each source file
        used_variables = []
        for file_path in vmc_path.rglob("*.f"):
            # Search in binary format
            with open(file_path, 'r') as f:
                content = f.read()
            if not definitions:
                break
            else:
                for variable in definitions:
                    pattern = f"{variable}"
                    start = re.search(pattern, content)
                    if start is not None:
                        used_variables.append(variable)
                        definitions.remove(variable)
        return used_variables


def split_variables_into_multiple_lines(variables: list) -> str:
    """Split the variable in lines of a maximun size."""
    def fun(lists): return sum(len(l) for l in lists)
    def max_size(i): return 40 if i == 0 else 60
    lines = [[]]
    index = 0
    for v in variables:
        acc = fun(lines[index])
        if acc > max_size(index):
            lines[index].append(v)
            lines.append([])
            index += 1
        else:
            lines[index].append(v)

    xs = list(filter(lambda x: x, [', '.join(group) for group in lines]))
    if xs[1:]:
        return f"{xs[0]},\n     &" + ',\n     &'.join(xs[1:])
    else:
        return f"{xs[0]}\n"


def search_end_recursively(lines: str, index: int, size: int = 80) -> int:
    """Search for the index of the last continuation line."""
    patt = r"^\s*&.*"
    while True:
        rs = re.search(patt, lines[index:])
        if rs is None:
            break
        else:
            index += rs.end()

    return index


def split_str_at_keyword(
        keyword: str, lines: str, multiline: bool = False, ignorecase: bool = False) -> str:
    """Split lines at `keyword` returning the lines before and after keyword."""
    flags = 0 if not ignorecase else re.IGNORECASE
    result = re.search(keyword, lines, flags=flags)
    sub = result.string
    if not multiline:
        return sub[:result.start()], sub[result.end():]
    else:
        end = search_end_recursively(lines, result.end())
        return sub[:result.start()], sub[end:]


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
    lists = s.splitlines()
    xss = takewhile(lambda line: len(line) > 0 and line.split()
                    [0].startswith("&"), lists)
    result = ''.join([x[1:] for x in xss])
    return result.replace('&', '')


def get_src_files(path: Path, folder: str):
    """List of the fortran 77 source files."""
    vmc_path = path / f"src/{folder}"
    return chain(sorted(vmc_path.glob("*.f")), sorted(vmc_path.glob("*.h")))


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
