"""Utilities to read a write data."""
from typing import List
import os

def read_file(filename: str) -> List[str]:
    """Read the data file and returns a list of strings

    :param filename: Name of the file to read.

    :return: Data in the file as typing List[].
    """

    with open(filename, 'r') as f:
        rawdata = f.readlines()

    return rawdata


def save_file(filename: str, rawdata: List[str]):
    """Print out the rawdata to a filename file.

    :param filename: Name of the file to read.

    :param rawdata: A rawdata typing List[] to be printed.
    """
    save_data = ''.join(rawdata)
    with open(filename, 'w') as f:
        f.write(save_data)

    print('=')
    print('= Output file written in %s' % filename)
    print('=')

    return


def get_new_filename(filename: str) -> str:
    """Get a new filename when --action clean_use or clean_implicit
    and NOT --overwrite flag.

    :param filename: File name parsed by the --filename flag.

    :return: New name composed as filename + _copy. + extension.
    """
    base_name = os.path.basename(filename)
    base, ext = base_name.split('.')
    fpath = os.path.dirname(filename)
    new_name = base +'_copy.' + ext
    return os.path.join(fpath,new_name)


def rise_error(file: str, function: str, type: str, message: str):
    """
    Rise errors according to arguments:

    :param file: Python file where the error occurs.

    :param function: Name of the function calling the error.

    :param type: Error type.

    :param message: String describing the error.
    """
    nl = '\n'
    if (type == "NameError"):
        msg = f'{nl}### ERROR ### {function} function/method' \
              f' in {file}:' \
              f'{nl}              "{message}"'
        raise NameError(msg)
    return
