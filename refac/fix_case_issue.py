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
            if spl[0] not in ['c', 'C', '!', 'implicit']:
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


def get_all_var(filename: str) -> List[str]:
    """[summary]

    Args:
        filename (str): [description]

    Returns:
        List[str]: [description]
    """
    rawdata = read_file(filename)
    data = process_data(rawdata)
    scope = separate_scope(data)

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


def count_var(filename: str, modules: SimpleNamespace) -> List[int]:
    """[summary]

    Args:
        scope (SimpleNamespace): [description]

    Returns:
        SimpleNamespace: [description]
    """

    data = process_data(read_file(filename))
    for m in modules:
        for var in m.var:
            c, srch = count(data, var.swapcase())
            if c > 0:
                print(' -- %s' % filename)
                print('    found %s of %s ' %
                      (var.swapcase(), m.name))
                # for s in srch:
                #     print('    ', s)

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
    pattern = re.compile('[\W\s]' + varname + '[\W\s]')
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

    scope, modules = get_all_var(args.modulefile)
    count_var(args.filename, modules)
