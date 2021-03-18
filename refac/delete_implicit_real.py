#!/usr/bin/env python
from types import SimpleNamespace
from typing import List, Optional, Tuple
import string
import re


def flatten_string_list(l: List[List[str]]) -> List[str]:
    """Flatten a list of list of str

    Args:
        l (List[List[str]]): [description]

    Returns:
        List[str]: [description]
    """
    return [item for sublist in l for item in sublist]


def split_string(s: str,
                 delimiters:
                 str =
                 r''' |
                 |, | ,|,|
                 |\= | \=|\=|
                 |\* | \*|\*|
                 |- | -|-|
                 |\+ | \+|\+|
                 |\( | \(|\(|
                 |\) | \)|\)|
                 |/ | /|/|
                 |\.eq\.|
                 |\.lt\.|
                 |\.gt\.|
                 |\.or\.|
                 |\.and\.|
                 |\.not\.|
                  ''') ->\
                 List[str]:
    """Split a string using the regex delimiters

    Args:
        s (str): the string
        delimiters (str, optional): Regex delimiters.
                                    Defaults to ' |, | ,|, | etc ...'.

    Returns:
        List[str]: the splitted string
    """
    split_str = re.split(delimiters, s)
    return list(filter(None, split_str))


def read_file(filename: str) -> List[str]:
    """Read the data file and returns a list of strings

    Args:
        filname (str): name of the file to read

    Returns:
        List[str]: data in the file
    """

    with open(filename, 'r') as f:
        rawdata = f.readlines()

    return rawdata


def replace_ampersand(rawdata: List[str]) -> List[List[str]]:
    """[summary]

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """

    for il, rd in enumerate(rawdata):
        if len(rd) > 0:
            if rd.lstrip(' ').startswith('use'):
                next_line = il+1
                while rawdata[next_line].lstrip(' ').startswith('&'):
                    name = rd.split()[1].lstrip(',').rstrip(',')
                    rawdata[next_line] = rawdata[next_line].replace(
                        '&', ' use %s, only: ' % name)
                    next_line += 1

    return rawdata


def substitute_implicit_real(rawdata: List[str]) -> List[List[str]]:
    """Substitute 'implicit real*8(a-h,o-z)' by 'implicit none'

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    for index, rd in enumerate(rawdata):
        if rd.lstrip(' ').startswith('implicit real*8(a-h,o-z)'):
            rawdata[index] = "      implicit none\n\n"
    return rawdata


def process_data(rawdata: List[str]) -> List[List[str]]:
    """Split the raw data into chunks

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """

    rawdata = substitute_implicit_real(rawdata)

    return [split_string(rd) if len(rd) > 0 else rd for rd in rawdata]


def separate_scope(data: List[str]) -> List[SimpleNamespace]:
    """Find the scope regions of the data

    Args:
        data (List[str]): data read in the file

    Returns:
        List[List[str]]: each scope separated
    """

    # identifier for scoping
    start_keyword = ['subroutine', 'function', 'program', 'module']
    end_keyword = ['end', 'end\n']

    # get the index of start/end scope
    name, idx_start, idx_end = [], [], []
    for i, d in enumerate(data):

        if len(d) == 0:
            continue

        if d[0] in start_keyword:
            idx_start.append(i)
            name.append(d[1].split('(')[0])

        if d[0] in end_keyword:
            idx_end.append(i)

    return [SimpleNamespace(name=name, istart=istart,
            data=data[istart:iend], module=[], bulky_var=[])
            for name, istart, iend in zip(name, idx_start, idx_end)]


def find_bulky_var(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Filter variables in the bulky scope.data that are not imported by
    the use statements.

    Args:
        :param scope: Namespace containing the data.

    Returns:
        :return scope: Return the same SimpleNamespace with the
                       scope.bulky_var attribute populated by a simple
                       list[] containing all the unique variables found
                       in scope.data that are not imported by the use imports.
    """
    # First we define keywords that we will exclude from the potential
    # set of variables found in scope.data:
    # -) Eg. we avoid lines with the following starting-words:
    avoid_analysis = ["implicit", "subroutine", "program", "endif", "enddo",
                      "return", "use", "!", "c", "C", "\n"]

    # -) Also, we know that Fortran keywords are not variables:
    exclude = ["&", "dimension", "if", "endif", "else", "elseif", "end",
               "do", "enddo",
               "then", "return", "\n"]

    # -) We add to the exclude keywords all variables imported by the
    # use statements:
    for s in scope.module:
        for v in s.var:
            exclude.append(v.name)

    # Second, we analyse the whole scope.data:
    bulky_var = []  # Will carry all the selected variables in scope.data.

    for s in scope.data:
        s_copy = []    # Will carry the selected variables per scope.data line.

        if len(s) == 0:
            continue

        if len(s) >= 2:  # avoid use without only statements.

            if s[0] in avoid_analysis:
                continue

            starting_point = 0

            # For that, first we exclude the "call xxx" that we
            # now the are not variables:
            if s[0] == "call" or s[0] == "entry":
                starting_point = 2

            # Now we start the main loop:
            for x in range(starting_point, len(s)):

                # Make sure that the potential variable is not a digit
                # and has no quotes:
                if (not s[x].strip("\n").isdigit()) and "\"" not in s[x] \
                  and "\'" not in s[x]:
                    variable = s[x].strip("\n")

                # Make sure it has some length, and is not in the
                # exclude list:
                    if len(variable) > 0 and variable not in exclude:
                        s_copy.append(variable)
                        bulky_var.append(s_copy)

    # Finish by deleting redundancies:
    scope.bulky_var = (list(dict.fromkeys(flatten_string_list(bulky_var))))

    return scope


def add_undeclared_variables(rawdata: List[str],
                             scope: SimpleNamespace, index: int) -> List[str]:
    """

    Args:
        rawdata (List[str]): [description]
        scope (SimpleNamespace): [description]
        index: index of scope in the precendent SimpleNamespace.

    Returns:
        List[str]: [description]
    """
    # Declare missed variables:
    if len(scope.bulky_var):
        new_variables_to_add = []  # Carries the declaration of new variables.
        new_integers = []
        new_floats = []
        for var in scope.bulky_var:
            integer_variables = string.ascii_lowercase[8:14]
            if var[0] in integer_variables:
                new_integers.extend(['      integer', ' :: ', var, "\n"])
            else:
                new_floats.extend(['      real*8', ' :: ', var, "\n"])
    new_variables_to_add = new_integers + new_floats

    # Add declared missed variables to raw data after an "implicit none"
    # declaration:
    implicit_indexes = list_duplicates(rawdata, "implicit none")
    rawdata[implicit_indexes[index]+1:
            implicit_indexes[index]] = new_variables_to_add

    return rawdata


def list_duplicates(seq, item):
    """Find indexes of duplicate items in a list.

    :param seq: Entry list[] to inspect.

    :param item: Item to look for in the seq list.

    :return indexes: Output list with the indexes where item appears. 
    """
    start_at = -1
    indexes = []

    # Fist, strip and lowercase the entry list:
    seq_copy = [rd.lstrip().strip("\n").lower() for rd in seq]

    while True:
        try:
            loc = seq_copy.index(item, start_at+1)
        except ValueError:
            break
        else:
            indexes.append(loc)
            start_at = loc
    return indexes


def get_new_filename(filename: str) -> str:
    """[summary]

    Args:
        filename (str): [description]

    Returns:
        str: [description]
    """

    base, ext = filename.split('.')
    return base + '_copy.' + ext


def save_file(filename: str, rawdata: List[str]):
    """[summary]

    Args:
        filename (str): [description]
        scope_data ([type]): [description]
    """
    save_data = ''.join(rawdata)
    with open(filename, 'w') as f:
        f.write(save_data)

    print('=')
    print('= Outpufile written in %s' % filename)
    print('=')


def clean_use_statement(filename: str, overwrite: bool = False) -> List[SimpleNamespace]:
    """[summary]

    Args:
        filename (str): [description]
        overwrite (bool): [description]
    """

    print('=')
    print('= Add undeclared variables in %s' % filename)
    print('=')

    # read the data file and split it
    rawdata = read_file(filename)

    # splitted data
    data = process_data(rawdata)

#    print("rawdata before the loop:", rawdata)
    # separate in scope
    scoped_data = separate_scope(data)

    # loop over scopes
    for index, scope in enumerate(scoped_data):

        print('  - Adding variables to scope : %s' % scope.name)

        # find variables in the bulky body of the scope:
        scope = find_bulky_var(scope)

        # add undeclared variables:
        rawdata = add_undeclared_variables(rawdata, scope, index)
        print('  - done!') 

    # save file copy
    if overwrite:
        save_file(filename, rawdata)
    else:
        new_filename = get_new_filename(filename)
        save_file(new_filename, rawdata)

    return scoped_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="clean_use filename")
    parser.add_argument("filename", help="name of the file to clean")
    parser.add_argument(
        '-ow', '--overwrite', action='store_true', help='overwrite the inputfile')
    args = parser.parse_args()

    scope = clean_use_statement(args.filename, args.overwrite)
