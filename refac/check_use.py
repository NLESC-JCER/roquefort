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


def split_string(s: str, delimiters: str = ' |, | ,|,') -> List[str]:
    """Split a string using the regex delimiters

    Args:
        s (str): the string
        delimiters (str, optional): regex delimiters. Defaults to ' |, | ,|,'.

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


def consider_line(spl: List[str]):
    comment = ['c', 'C', '!']
    if spl[0] in comment:
        return False
    if spl[0] == 'implicit':
        return False
    if spl[0].startswith('format'):
        return False
    if spl[0].startswith('write'):
        return False
    if len(spl) == 1 and spl[0][0] in comment:
        return False
    else:
        return True


def process_data(rawdata: List[str]) -> List[List[str]]:
    """Split the raw data into chunks

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    out = []
    for rd in rawdata:
        if len(rd) > 0:
            spl = split_string(rd)
            if consider_line(spl):
                out.append(spl)
    return out
    # return [split_string(rd) if len(rd) > 0 else rd for rd in rawdata]


def separate_scope(data: List[str]) -> List[SimpleNamespace]:
    """Find the scope regions of the data

    Args:
        data (List[str]): data read in the file

    Returns:
        List[List[str]]: each scope separated
    """

    # identifier for scoping
    start_keyword = ['subroutine', 'function', 'module']
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

    return [SimpleNamespace(name=name, istart=istart, data=data[istart:iend]) for name, istart, iend in zip(name, idx_start, idx_end)]


def get_scope(filename: str) -> SimpleNamespace:
    """[summary]

    Args:
        filename (str): [description]

    Returns:
        SimpleNamespace: [description]
    """

    rawdata = read_file(filename)
    data = process_data(rawdata)
    return separate_scope(data)


def get_all_var(filename: str) -> List[str]:
    """[summary]

    Args:
        filename (str): [description]

    Returns:
        List[str]: [description]
    """
    scope = get_scope(filename)

    modules = []

    for s in scope:

        var = []
        for d in s.data:

            if d[0] == 'public':

                for varname in d[2:]:
                    if varname == '\n':
                        continue
                    var.append(varname.rstrip('\n'))

        modules.append(SimpleNamespace(name=s.name, var=var))

    return scope, modules


def get_use_vars(scope: SimpleNamespace) -> List:
    """Find variable that are imported in the scope

    Args:
        scope_data (List[str]): data of the scope

    Returns:
        SimpleNamespace: namespace containing name, iline, icol of each var in scope
    """
    use_vars = []
    for iline, s in enumerate(scope.data):

        if len(s) == 0:
            continue

        if s[0] == 'use' and s[2].startswith('only'):

            module_name = s[1].rstrip('\n')

            for icol in range(3, len(s)):
                varname = s[icol].rstrip('\n')
                if len(varname) > 0:
                    use_vars.append(varname)

    return use_vars


def is_declaration(s):
    declaration_kwrd = ['integer', 'real', 'dimenion', 'parameter']
    for kw in declaration_kwrd:
        if s[0].startswith(kw):
            return True


def get_local_vars(scope: SimpleNamespace) -> List:
    """[summary]

    Args:
        scope (SimpleNamespace): [description]

    Returns:
        List: [description]
    """

    local_vars = []
    for iline, s in enumerate(scope.data):

        if len(s) == 0:
            continue

        if is_declaration(s):
            for icol in range(1, len(s)):
                varname = s[icol].split('(')[0].rstrip('\n')
                if len(varname) > 0:
                    local_vars.append(varname)

        if s[0] == ('common'):
            for icol in range(2, len(s)):
                varname = s[icol].split('(')[0].rstrip('\n')
                if len(varname) > 0:
                    local_vars.append(varname)

    return local_vars


def check_var(scope: List[SimpleNamespace], modules: List[SimpleNamespace]) -> List[int]:
    """[summary]

    Args:
        scope (SimpleNamespace): [description]

    Returns:
        SimpleNamespace: [description]
    """

    for s in scope:
        print_scope_name = True

        use_var = get_use_vars(s)
        local_var = get_local_vars(s)

        for m in modules:
            for var in m.var:
                if len(var) < 4:
                    continue
                c0, srch = count([s.data[0]], var)
                c, srch = count(s.data[1:], var)
                if c0 == 0 and var not in local_var:
                    if c > 0 and var not in use_var:
                        if print_scope_name:
                            print('\n -- Scope : %s' %
                                  s.name.rstrip('\n'))
                            print_scope_name = False
                        print('    missing variable %s from module %s' %
                              (var.rstrip('\n'), m.name.rstrip('\n')))
                        if var.rstrip('\n') == 'c':
                            for ls in srch:
                                print('    ', ls)


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
    c = len(pattern.findall(joined_data))
    contxt = []
    if c > 0:
        srch = pattern.finditer(joined_data)
        for s in srch:
            contxt.append(joined_data[s.span()[0]-5:s.span()[1]+5])
    return c, contxt


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="clean_use filename")
    parser.add_argument("filename", help="name of the file to clean")

    parser.add_argument(
        "modulefile", help="name of the file where to find the module")

    parser.add_argument(
        '-ow', '--overwrite', action='store_true', help='overwrite the inputfile')
    args = parser.parse_args()

    print("== FILE : %s" % args.filename)
    # get all modules and their variables
    mod_scope, modules = get_all_var(args.modulefile)

    # get all the scopes
    scope = get_scope(args.filename)

    # check
    check_var(scope, modules)
