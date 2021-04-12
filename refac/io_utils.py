"""Utilities to read a write data."""
from typing import List


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
    base, ext = filename.split('.')
    return base + '_copy.' + ext
