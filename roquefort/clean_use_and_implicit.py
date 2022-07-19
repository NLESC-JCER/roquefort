#!/usr/bin/env python
import os
from types import SimpleNamespace
from typing import List
from roquefort.io_utils import read_file, save_file, get_new_filename, rise_error
from roquefort.scope_utils import separate_scope, fill_scopes, modify_rawdata, modify_rawdata_move_var
from roquefort.string_utils import split_rawdata
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
            if rd.lstrip(' ').startswith('parameter'):
                if rd.lstrip(' ').startswith('parameter('):
                    rawdata[il] = \
                        rawdata[il].replace(
                            "parameter(", "parameter (")
                next_line = il+1
                while rawdata[next_line].lstrip(' ').startswith('&'):
                    rawdata[il] = rawdata[il].rstrip(
                        "\n").rstrip(",") + ")"
                    rawdata[next_line] = rawdata[next_line].\
                        replace('&,', '&').replace(
                            '&', ' parameter (')
                    next_line += 1
            if rd.lstrip(' ').startswith('dimension'):
                next_line = il+1
                while rawdata[next_line].lstrip(' ').startswith('&'):
                    rawdata[next_line] = rawdata[next_line].\
                        replace('&,', '&').replace('&', ' dimension ')
                    next_line += 1
    return rawdata


def replace_implicit_real(rawdata: List[str]) -> List[str]:
    """Replace 'implicit real*8(a-h,o-z)' by 'implicit none'.

    :param rawdata: Plain rawdata as read from the read_file function.

    :return: rawdata input with the implicit real replaced by none.
    """
    implicit_declaration = False
    for index, rd in enumerate(rawdata):
        if rd.lstrip(' ').lower().startswith('implicit none'):
            rise_error(file=os.path.basename(__file__),
                       function=replace_implicit_real.__name__,
                       type='NameError',
                       message="Implicit none is already declared!")
            implicit_declaration = True
        elif rd.lstrip(' ').lower().startswith('implicit real*8'):
            rawdata[index] = "      implicit none\n\n"
            implicit_declaration = True

    if not implicit_declaration:
        rise_error(file=os.path.basename(__file__),
                   function=replace_implicit_real.__name__,
                   type='NameError',
                   message="There is no implicit declaration!")
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

def move_variable(args: argparse.ArgumentParser) -> \
        List[SimpleNamespace]:
    """Move a variable from one module to another

    :param args: argparse arguments, namely:
                    args.filename,
                    args.overwrite.

    :return: List[] of SimpleNamespace cotaining the scooped data.
    """
    print('=')
    print('= Move variable %s to module %s in file %s' % (args.var_name, args.new_module, args.filename))
    print('=')



    # Read the data file and split it:
    rawdata = read_file(args.filename)
    
    # Prepare data to be splitted in scopes, remove &'s, implicit real, etc:
    data = process_data(rawdata, clean_implicit=False)
   
    # Separate in scope:
    scopes = separate_scope(data)
    
    # Fill attributes of scopes:
    scopes = fill_scopes(rawdata, scopes, clean_implicit=False)
    
    # Modify rawdata according to scopes and flag options:
    modified_rawdata, rewrite = modify_rawdata_move_var(rawdata, scopes, 
                                       args.var_name, args.new_module, args.from_module)

    # save file copy
    if rewrite:
        if args.overwrite:
            save_file(args.filename, modified_rawdata)
        else:
            new_filename = get_new_filename(args.filename)
            save_file(new_filename, modified_rawdata)

    return scopes

