#!/usr/bin/env python
from types import SimpleNamespace
from typing import List, Optional, Tuple
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


def remove_use_without_only(rawdata: List[str]) -> List[List[str]]:
    """Remove the "use" lines without a "only" statment.

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    for rd in rawdata:
        if len(rd) > 0:
            if rd.lstrip(' ').startswith('use') and "only" not in rd:
                rawdata.remove(rd)
    return rawdata


def remove_commented_lines(rawdata: List[str]) -> List[List[str]]:
    """Remove lines starting with "c ", "C ", "! "

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    for rd in rawdata:
        if len(rd) > 0:
            if rd.startswith('c ') or rd.startswith('C ') or \
               rd.startswith('! '):
                rawdata.remove(rd)
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
            rawdata[index] = "implicit none"
    return rawdata


def process_data(rawdata: List[str]) -> List[List[str]]:
    """Split the raw data into chunks

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """

    rawdata = substitute_implicit_real(rawdata)
    rawdata = replace_ampersand(rawdata)
    rawdata = remove_use_without_only(rawdata)
    rawdata = remove_commented_lines(rawdata)

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


def find_import_var(scope: SimpleNamespace) -> SimpleNamespace:
    """Find variable that are imported in the scope

    Args:
        scope_data (List[str]): data of the scope

    Returns:
        SimpleNamespace: namespace containing name, iline, icol of each var in scope
    """

    for iline, s in enumerate(scope.data):

        if len(s) == 0:
            continue

        if len(s) == 2 and s[0] == "use":
            continue

        if len(s) >= 2:
            if s[0] == 'use' and s[2].startswith('only'):

                module_name = s[1].rstrip('\n')
                mod = SimpleNamespace(
                    name=module_name, iline=iline, total_count=0)
                mod.var = []

                for icol in range(3, len(s)):
                    varname = s[icol].rstrip('\n')
                    if len(varname) > 0:
                        mod.var.append(SimpleNamespace(name=varname,
                                                       count=None))

                scope.module.append(mod)

    return scope


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
                      "return", "\n"]

    # -) Also, we know that Fortran keywords are not variables:
    exclude = ["&", "dimension", "if", "endif", "else", "elseif", "end",
               "do", "enddo",
               "then", "return", "\n"]

    # -) We add to the eclude keywords all variables imported by the
    # use statments:
    for s in scope.module:
        for v in s.var:
            exclude.append(v.name)

    # Second, we analyse the whole scope.data:
    bulky_var = []  # Will carry all the selected variables in scope.data.

    for iline, s in enumerate(scope.data):

        s_copy = []    # Will carry the selected variables per scope.data line.

        if len(s) == 0:
            continue

        if s[0] == 'use' and s[2].startswith('only'):
            continue

        if len(s) > 0:

            if s[0] in avoid_analysis:
                continue

            starting_point = 0

            # For that, first we exclude the "call xxx" that we
            # now the are not variables:
            if s[0] == "call":
                starting_point = 2

            # Now we start the main loop:
            for x in range(starting_point, len(s)):

                # Make sure that the potential variable is not a digit
                # and has no quotes:
                if (not s[x].strip("\n").isdigit()) and "\"" not in s[x] \
                  and "\'" not in s[x]:
                    variable = s[x].strip("\n")

                # Make sure it has some lenght, and is not in the
                # exclude list:
                    if len(variable) > 0 and variable not in exclude:
                        s_copy.append(variable)
                        bulky_var.append(s_copy)

    # Once it is done, append the scope.bulky_var attribute:
    scope.bulky_var.append(list(dict.fromkeys(flatten_string_list(bulky_var))))

    return scope


def count_var(scope: SimpleNamespace) -> SimpleNamespace:
    """[summary]

    Args:
        scope (SimpleNamespace): [description]

    Returns:
        SimpleNamespace: [description]
    """
    # Avoid to count variables in commented lines:
    exclude = ["c", "C", "!"]
    data_copy = [var for index, var in enumerate(scope.data)
                 if var[0] not in exclude]

    for mod in scope.module:
        for var in mod.var:
            c = count(data_copy, var.name)
            var.count = c
            mod.total_count += c
    return scope

def count(scope_data: List[str], varname: str) -> int:
    """Count the number of time a variable appears in the

    Args:
        scope_data (List[str]): data of the scope
        var (str): name of the vairable

    Returns:
        int: count
    """
    joined_data = ' ' + \
        ' '.join(flatten_string_list(scope_data)) + ' '
    pattern = re.compile('[\W\s]' + varname + '[\W\s]', re.IGNORECASE)
    return len(pattern.findall(joined_data))-1


def clean_raw_data(rawdata: List[str], scope: SimpleNamespace) -> List[str]:
    """

    Args:
        rawdata (List[str]): [description]
        scope (SimpleNamespace): [description]

    Returns:
        List[str]: [description]
    """

    for mod in scope.module:

        print('  --  Module : %s' % mod.name)
        idx_rawdata = scope.istart + mod.iline

        if mod.total_count == 0:
            print('      No variable called, removing the entire module')
            rawdata[idx_rawdata] = ''
            idx_rawdata += 1
            while rawdata[idx_rawdata].lstrip(' ').startswith('&'):
                rawdata[idx_rawdata] = ''
                idx_rawdata += 1

        else:

            ori_line = rawdata[idx_rawdata]
            line = ori_line.split(
                'use')[0] + 'use ' + mod.name + ', only: '

            for var in mod.var:
                if var.count != 0:
                    line += var.name + ', '
                else:
                    print('  ---   removing unused variable %s' %
                          var.name)
            rawdata[idx_rawdata] = line.rstrip(', ') + '\n'

            # remove the unwanted
            idx_rawdata += 1
            while rawdata[idx_rawdata].lstrip(' ').startswith('&'):
                rawdata[idx_rawdata] = ''
                idx_rawdata += 1

    return rawdata


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
    print('= Clean Use Statements from %s' % filename)
    print('=')

    # read the data file and split it
    rawdata = read_file(filename)

    # splitted data
    data = process_data(rawdata)

    # separate in scope
    scoped_data = separate_scope(data)
#    for i in scoped_data:
#        print("Pablo NameSpace name:", i.name, "\n")
#        print("Pablo NameSpace istart:", i.istart, "\n")
#        print("Pablo NameSpace module:", i.module, "\n")

    # loop over scopes
    for scope in scoped_data:

        print('  - Scope : %s' % scope.name)

        # find variables
        scope = find_import_var(scope)
        scope = find_bulky_var(scope)
        print("Pablo prints one scope END:", scope)
#        print(scope)
#        for i in scope.bulky_var:
#            print("Pablo", type(i))
#            print("Pablo", i.var)
#                for j in i.var:
#                    print("Element", j.name)
#
#        # count the number of var calls per var per module in scope
#        scope = count_var(scope)
#
#        # clean the raw data
#        rawdata = clean_raw_data(rawdata, scope)
#
    # save file copy
    if overwrite:
        save_file(filename, rawdata)
    else:
        new_filename = get_new_filename(filename)
        save_file(new_filename, rawdata)

    return #scoped_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="clean_use filename")
    parser.add_argument("filename", help="name of the file to clean")
    parser.add_argument(
        '-ow', '--overwrite', action='store_true', help='overwrite the inputfile')
    args = parser.parse_args()

    scope = clean_use_statement(args.filename, args.overwrite)
