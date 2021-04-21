""" Utilities for string manipulation."""
from typing import List
import re


def split_rawdata(rawdata: List[str]) -> List[str]:
    """Separate rawdata according to different patterns."""
    rawdata_split = []
    for rd in rawdata:
        if rd.lstrip(" ")[0:9] == "parameter":
            rawdata_split.append(split_string_soft(rd))
        elif rd.lstrip(" ")[0:9] == "dimension":
            rawdata_split.append(split_string_soft(rd))
        else:
            rawdata_split.append(split_string_hard(rd))
    return rawdata_split


def flatten_string_list(l: List[List[str]]) -> List[str]:
    """Flatten a list of list of str

    Args:
        l (List[List[str]]): [description]

    Returns:
        List[str]: [description]
    """
    return [item for sublist in l for item in sublist]


def split_string_soft(s: str,
                      delimiters:
                      str =
                      r''' |
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


def split_string_medium(s: str,
                        delimiters:
                        str =
                        r''' |
                        |, | ,|,|
                        |: | :|:|
                        |\= | \=|\=|
                        |\( | \(|\(|
                        |\) | \)|\)|
                        |\> | \>|\>|
                        |\< | \<|\<|
                        |\$ | \$|\$|
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


def split_string_hard(s: str,
                      delimiters:
                      str =
                      r''' |
                      |, | ,|,|
                      |: | :|:|
                      |\= | \=|\=|
                      |\* | \*|\*|
                      |- | -|-|
                      |\+ | \+|\+|
                      |\( | \(|\(|
                      |\) | \)|\)|
                      |\> | \>|\>|
                      |\< | \<|\<|
                      |\$ | \$|\$|
                      |/ | /|/|
                      |\.eq\.|
                      |\.lt\.|
                      |\.le\.|
                      |\.gt\.|
                      |\.ge\.|
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


def has_number(input_string: str) -> bool:
    """Returns True if the entry string has a number.

    :param input_string: str

    :return: boolean
    """
    return any(char.isdigit() for char in input_string)
