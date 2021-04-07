#!/usr/bin/env python
from types import SimpleNamespace
from typing import List, Optional, Tuple
import string
import argparse
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
        if rd.lstrip(' ').startswith('implicit real*8'):
            rawdata[index] = "      implicit none\n\n"
    return rawdata


def delete_parameters(rawdata: List[str]) -> List[List[str]]:
    """Delete lines starting with the word paramter, e.g:
       paramter(zero =0.d0, one=1.0d0)

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    rawdata = [rd for rd in rawdata if not( 
               rd.lstrip(" ").startswith("parameter")
               and len(rd.lstrip(" ")) > 9)]

    return rawdata


def process_data(rawdata: List[str], clean_implicit: bool) -> List[List[str]]:
    """Split the raw data into chunks

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """

    if clean_implicit:
        rawdata = substitute_implicit_real(rawdata)
    rawdata = replace_ampersand(rawdata)

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
            data=data[istart:iend], module=[], parameters=[], bulky_var=[])
            for name, istart, iend in zip(name, idx_start, idx_end)]


def find_import_var(scope: SimpleNamespace) -> SimpleNamespace:
    """Find variable that are imported in the scope

    Args:
        scope_data (List[str]): data of the scope.

    Returns:
        SimpleNamespace: namespace containing name, iline, icol of
                         each var in scope.
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


def find_parameters(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.parameters = list[] with parameter-declared variables.
    E.g.: 'parameter(zero=0.d0, one=1.d0)'

    Args:
        :param scope: Namespace containing the data.

    Returns:
        :return scope: Return the same SimpleNamespace with the
                       scope.parameters attribute populated by a simple
                       list[] containing all the variables declared as
                       parameters.
    """
    for sd in scope.data:
        if sd[0].lower() == "parameter":
            sd_strip = []   # a copy of sd without ending lines.
            bulky_parameters = []   # parameters found per line.
            starting_point = 1
            for var in sd:
                sd_strip.append(var.strip("\n"))

            # Start the main loop:
            s_iter = iter(x for x in sd_strip[starting_point:] if len(x))
            for x in s_iter:
                bulky_parameters.append(x)

    # Finish by deleting redundancies:
    scope.parameters = (list(dict.fromkeys(bulky_parameters)))
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
    # Avoid lines with the following starting-words:
    avoid_analysis = ["implicit", "subroutine", "program", "endif", "enddo",
                      "return", "continue", "!", "c", "C", "function", "use",
                      "go", "goto",
                      "\n"]

    # Avoid Fortran keywords that are not variables:
    exclude = ["&", "dimension", "parameter", "if", "endif", "else", "elseif",
               "end", "open", "close", "do", "call", "write", "goto", "enddo",
               "then", "to", "return", "min", "max", "nint", "abs", "float",
               "data", "log", "dlog", "exp", "dexp", "mod", "sign", "int",
               "status", "format", "file", "unit", "read", "save", "rewind",
               "character", "backspace",
               "dfloat", "dsqrt", "dcos", "dsin", "sqrt", "continue",
               "mpi_status_size", "mpi_integer", "mpi_sum", "mpi_max",
               "mpi_comm_world", "mpi_double_precision",
               "\n"]

    # Initiate booleans to discern quotes:
    in_quotes = False
    double_quote = False
    quoted_one_word = False
    quoted_sign = ""

    # Exclude all variables imported by the use statements:
    for s in scope.module:
        for v in s.var:
            exclude.append(v.name.lower())

    # Exclude all variables declared as parameters:
    for s in scope.parameters:
        exclude.append(s)

    # Analyse the whole scope.data:
    bulky_var = []  # carry all the selected variables in scope.data.

    for sd in scope.data:
        sd_copy = []    # carry the selected variables per scope.data line.
        sd_strip = []   # a copy of sd without ending lines.

        for var in sd:
            sd_strip.append(var.strip("\n"))

        if len(sd_strip) == 0:
            continue

        # Avoid use without only statements:
        if len(sd_strip) == 2 and sd_strip[0] == "use":
            continue

        if len(sd_strip) >= 2:

            if sd_strip[0] in avoid_analysis:
                continue

            # Add variables declared as characters to the exclude list:
            if sd_strip[0].lower() == "character":
                character_var = [x for x in sd_strip[1:] if not x.isdigit()]
                exclude.extend(character_var)

            starting_point = 0

            # Exclude xxx in call to subroutines/functions like "call xxx":
            if sd_strip[0] == "call" or sd_strip[0] == "entry":
                starting_point = 2

            # Exclude xxx in call to subroutines/functions like "21 call xxx":
            if (sd_strip[0].isdigit() or sd_strip[0] == "&") and \
               sd_strip[1] == "call":
                starting_point = 3

            # Start the main loop:
            s_iter = iter(x for x in sd_strip[starting_point:] if len(x))
            for x in s_iter:
                # Skip xxx variables in lines like: if() call xxx():
                if x == "call":
                    next(s_iter)
                    next(s_iter)

                # Deal with quotes ', '', ":
                if not in_quotes:
                    if x[0] == "\'":
                        if len(x) > 1:
                            if x[:2] == "\'\'":
                                quoted_sign = "\'\'"
                                double_quote = True
                            else:
                                quoted_sign = "\'"
                        else:
                            quoted_sign = "\'"

                    if x[0] == "\"":
                        quoted_sign = "\""

                    if quoted_sign:
                        in_quotes = True

                    # Deal with quoted one-words:
                    if len(x) > 2:
                        if double_quote and x[-2:] == quoted_sign:
                            quoted_one_word = True
                        if (not double_quote) and x[-1:] == quoted_sign:
                            quoted_one_word = True
                else:
                    if len(x) > 1:
                        if double_quote:
                            if x[-2:] == quoted_sign:
                                in_quotes = False
                                double_quote = False
                                quoted_sign = ""
                        else:
                            if x[-1:] == quoted_sign and x[-2:] != "\'\'":
                                in_quotes = False
                                quoted_sign = ""
                    else:
                        if x[-1:] == quoted_sign:
                            in_quotes = False
                            quoted_sign = ""

                # Make sure that the potential variable is not a digit
                # and has no point or ampersand, and is not a single-quoted
                # word or quoted text:
                if (not x.isdigit()) and \
                   not any(a in x for a in (".", "&", "\'", "\"")) \
                   and not in_quotes:
                    variable = x

                # Make sure it has some length, and is not in the
                # exclude list:
                    if len(variable) > 0 and variable.lower() \
                       not in exclude:
                        sd_copy.append(variable)
                        bulky_var.append(sd_copy)

                # Reset booleans if x is a quoted_one_word:
                if quoted_one_word:
                    quoted_one_word = False
                    in_quotes = False
                    if double_quote:
                        double_quote = False
                    quoted_sign = ""

    # Finish by deleting redundancies:
    scope.bulky_var = (list(dict.fromkeys(flatten_string_list(bulky_var))))
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


def clean_raw_data(rawdata: List[str],
                   scope: SimpleNamespace) -> List[str]:
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
    # List of integers and floats to add:
    new_integers = ['      integer', ' :: ']
    new_floats = ['      real(dp)', ' :: ']
    new_float_parameters = []

    # Declare missed variables:
    new_variables_to_add = []  # Carries the declaration of new variables.

    index_integer = 1
    index_float = 1
    max_line_length = 10
    new_integer_line = False
    new_float_line = False

    for var in sorted(scope.bulky_var):
        integer_variables = string.ascii_lowercase[8:14]

        # Collect potential integer variables:
        if var[0] in integer_variables:
            if len(new_integers) >= max_line_length * index_integer:
                index_integer += 1
                new_integers.extend(["\n", '      integer', ' :: '])
                new_integer_line = True

            if len(new_integers) > 2:
                if new_integer_line:
                    new_integers.extend([var])
                    new_integer_line = False
                else:
                    new_integers.extend([", ", var])
            else:
                new_integers.extend([var])

        # Collect potential float variables:
        else:
            if len(new_floats) >= max_line_length * index_float:
                index_float += 1
                new_floats.extend(["\n", '      real(dp)', ' :: '])
                new_float_line = True

            if len(new_floats) > 2:
                if new_float_line:
                    new_floats.extend([var])
                    new_float_line = False
                else:
                    new_floats.extend([", ", var])
            else:
                new_floats.extend([var])

    # Empty the list if there are not elements:
    if len(new_integers) == 2:
        new_integers = []
    if len(new_floats) == 2:
        new_floats = []

    # Add variables declared as parameters:
    if len(scope.parameters):
        for index_sp in range(0, len(scope.parameters), 2):
            new_float_parameters.extend([
                '      real(dp)', ', ', 'parameter', ' :: ',
                scope.parameters[index_sp], " = ",
                scope.parameters[index_sp+1],
                "\n"])

    # Add final new line and combine:
    new_integers.append("\n")
    new_floats.append("\n")
    new_variables_to_add = new_integers + new_floats + new_float_parameters

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


def clean_statements(args: argparse.ArgumentParser) -> \
                        List[SimpleNamespace]:
    """Clean 'use' or 'implicit real' statements according to argparse arguments.
        Writes result to args.filename_copy.f (or .F, or f90 ...) file if the
        overwrite, -ow, flag is not provided.

    :param args: argparse arguments, namely:
                    args.filename,
                    args.clean_use,
                    args.clean_implicit
                    args.overwrite.

    :return: List[] of SimpleNamespace cotaining the scooped data.
    """
    print('=')
    print('= Clean Use Statements from %s' % args.filename)
    print('=')

    # read the data file and split it
    rawdata = read_file(args.filename)

    # Prepare data to be splitted in scopes, remove &'s, implicit real, etc:
    data = process_data(rawdata, args.clean_implicit)

    # separate in scope
    scoped_data = separate_scope(data)

    # loop over scopes
    for index, scope in enumerate(scoped_data):

        print('  - Scope : %s' % scope.name)

        # Find variables in use statements:
        scope = find_import_var(scope)

        # Find possible variables on the bulky of the scope:
        if args.clean_implicit:
            scope = find_parameters(scope)
            scope = find_bulky_var(scope)

        if args.clean_use:
            # Count the number of var calls per var per module in scope:
            scope = count_var(scope)

            # clean the raw data
            rawdata = clean_raw_data(rawdata, scope)

        # add undeclared variables:
        if args.clean_implicit:
            if len(scope.bulky_var):
                rawdata = add_undeclared_variables(rawdata, scope, index)
                rawdata = delete_parameters(rawdata)
            else:
                print('      No potential variables found in the scope.')

        print('    ... done!\n')

    # save file copy
    if args.overwrite:
        save_file(args.filename, rawdata)
    else:
        new_filename = get_new_filename(args.filename)
        save_file(new_filename, rawdata)

    return scoped_data


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="clean 'use' or \
                                     'implicit real' statements in filename")

    parser.add_argument("filename", help="name of the file to clean")

    # Clean of "use" statements:
    parser.add_argument(
        '--clean_use', action='store_true',
        help="clean variables not use in 'use' statements")

    # Replace "implicit real" by "implicit none":
    parser.add_argument(
        '--clean_implicit', action='store_true',
        help="replace 'implicit real' by 'implicit none' statements")

    # Overwrite the file?
    parser.add_argument(
        '-ow', '--overwrite', action='store_true',
        help='overwrite the inputfile')

    args = parser.parse_args()

# Do a clean_use by default?
#    if args.clean_use + args.clean_implicit == 0:
#        args.clean_use = True

    if (args.clean_use and args.clean_implicit):
        raise parser.error("\nChoose only one action:"
                           " --clean_use or --clean_implicit")

    elif (args.clean_use or args.clean_implicit):
        scope = clean_statements(args)

    else:
        raise parser.error("\nChoose an argument action:"
                           " --clean_use or --clean_implicit")
