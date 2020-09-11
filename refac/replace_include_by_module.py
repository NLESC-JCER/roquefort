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
    return [split_string(rd) if len(rd) > 0 else rd for rd in rawdata]


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


def find_include(scope: SimpleNamespace, include_name: str) -> SimpleNamespace:
    """[summary]

    Args:
        scope (SimpleNamespace): [description]
        include_name (str): [description]

    Returns:
        SimpleNamespace: [description]
    """
    match_name = "'" + include_name + "'"
    for d in scope.data:
        if len(d) > 1:
            if d[0] == 'include' and d[1].rstrip('\n') == match_name:

                return True
    return False


def insert_index(scope: SimpleNamespace) -> int:
    """

    Args:
        scope (SimpleNamespace): [description]

    Returns:
        int: [description]
    """
    idx = []
    for i, s in enumerate(scope.data):
        if s[0] == 'use':
            idx.append(i)
    if idx == []:
        idx = [1]
    return idx


def assemble_use_statement(filename: str, modulename: str) -> List[str]:
    """[summary]

    Args:
        filename (str): [description]
        modulename (str): [description]

    Returns:
        List[str]: [description]
    """
    rawdata = read_file(filename)
    data = process_data(rawdata)
    scope = separate_scope(data)

    for s in scope:
        if s.name.rstrip('\n') == modulename:
            module_scope = s

    out = []
    for d in module_scope.data:
        if d[0] == 'public':
            line = 'use %s, only: ' % modulename
            for varname in d[2:]:
                if varname == '\n':
                    continue
                vn = varname.rstrip('\n')
                line += vn + ', '
            line = line.rstrip(', ')
            line += '\n'
            out.append(line)
    return out


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


def replace_include_by_module(filename: str,
                              modulefile: str,
                              modulename: str,
                              includename: str,
                              overwrite: bool = False) -> List[SimpleNamespace]:
    """[summary]

    Args:
        filename (str): [description]
        overwrite (bool): [description]
    """

    print('=')
    print('= File %s' % filename)
    print('= Replace include %s by module %s found in %s ' %
          (includename, modulename, modulefile))
    print('=')

    insert_lines = assemble_use_statement(
        modulefile, modulename)

    # read the data file and split it
    rawdata = read_file(filename)

    # splitted data
    data = process_data(rawdata)

    # separate in scope
    scoped_data = separate_scope(data)

    # loop over scopes
    n_added_lines = 0
    for scope in scoped_data:

        print('  - Scope : %s' % scope.name)
        if find_include(scope, includename):
            idx = insert_index(scope)
            idx_ = scope.istart + idx[0] + n_added_lines

            nws = len(rawdata[idx_]) - len(rawdata[idx_].lstrip(' '))
            if nws == 0:
                nws = 6

            for il, l in enumerate(insert_lines):
                print('    insert %s at line %d' %
                      (l.rstrip('\n'), idx_))
                rawdata.insert(idx_+il, ' '*nws + l)
                n_added_lines += 1

    for il, d in enumerate(rawdata):
        match_name = "include '%s'" % includename
        if d.lstrip(' ').rstrip(' ').rstrip('\n') == match_name:
            print('   remove include at line ', il)
            rawdata[il] = ''

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
        "includename", help="name of the include file")
    parser.add_argument(
        "modulefile", help="name of the file where to find the module")
    parser.add_argument(
        "modulename", help="name of the module to use")

    parser.add_argument(
        '-ow', '--overwrite', action='store_true', help='overwrite the inputfile')
    args = parser.parse_args()

    scope = replace_include_by_module(
        args.filename, args.modulefile, args.modulename, args.includename, args.overwrite)
