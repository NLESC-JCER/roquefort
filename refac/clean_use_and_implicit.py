#!/usr/bin/env python
from types import SimpleNamespace
from typing import List
from refac.io_utils import read_file, save_file, get_new_filename
from refac.scope_utils import separate_scope, fill_scopes, modify_rawdata
from refac.string_utils import split_rawdata
import argparse


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


def replace_implicit_real(rawdata: List[str]) -> List[str]:
    """Replace 'implicit real*8(a-h,o-z)' by 'implicit none'.

    :param rawdata: Plain rawdata as read from the read_file function.

    :return: rawdata input with the implicit real replaced by none.
    """
    for index, rd in enumerate(rawdata):
        if rd.lstrip(' ').startswith('implicit real*8'):
            rawdata[index] = "      implicit none\n\n"
    return rawdata


def process_data(rawdata: List[str], clean_implicit: bool) -> List[List[str]]:
    """Split the raw data into chunks

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """

    if clean_implicit:
        rawdata = replace_implicit_real(rawdata)
    rawdata = replace_ampersand(rawdata)
    rawdata = split_rawdata(rawdata)
    return rawdata


def clean_statements(args: argparse.ArgumentParser) -> \
                        List[SimpleNamespace]:
    """Clean 'use' or 'implicit real' statements according to argparse arguments.
        Writes result to args.filename_copy.f (or .F, or f90 ...) file if the
        overwrite, -ow, flag is not provided.

    :param args: argparse arguments, namely:
                    args.filename,
                    args.overwrite.

    :return: List[] of SimpleNamespace cotaining the scooped data.
    """
    print('=')
    print('= Clean Use Statements from %s' % args.filename)
    print('=')

    clean_use = False
    clean_implicit = False

    if args.command == "clean_use":
        clean_use = True
    elif args.command == "clean_implicit":
        clean_implicit = True

    # Read the data file and split it:
    rawdata = read_file(args.filename)

    # Prepare data to be splitted in scopes, remove &'s, implicit real, etc:
    data = process_data(rawdata, clean_implicit)

    # Separate in scope:
    scopes = separate_scope(data)

    # Fill attributes of scopes:
    scopes = fill_scopes(rawdata, scopes, clean_implicit)

    # Modify rawdata according to scopes and flag options:
    modified_rawdata = modify_rawdata(rawdata,
                                      scopes, clean_use, clean_implicit)

    # save file copy
    if args.overwrite:
        save_file(args.filename, modified_rawdata)
    else:
        new_filename = get_new_filename(args.filename)
        save_file(new_filename, modified_rawdata)

    return scopes
