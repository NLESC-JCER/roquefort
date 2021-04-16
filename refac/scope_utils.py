""" Utilities to build-up scopes."""
from typing import List
from types import SimpleNamespace
from refac.string_utils import flatten_string_list
import string
import re


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
            data=data[istart:iend], module=[], parameters=[], dimensions=[],
                      bulky_var=[])
            for name, istart, iend in zip(name, idx_start, idx_end)]


def fill_scopes(rawdata: List[str], scopes: List[SimpleNamespace],
                clean_implicit: bool) -> List[SimpleNamespace]:
    """Fills attributes of SimpleNamespace scopes.

    :param rawdata: List of the bulky content of the read file.

    :param scopes: List of scopes.

    :param clean_implicit: Boolean to replace or not the implicit real.

    :param return: List of entry scopes with attributes populated.
    """
    for scope in scopes:

        print('  - Adding scope: %s' % scope.name)
        # Find variables in use statements:
        print('  \t+ Filling module attribute.')
        scope = fill_module(scope)

        # Find possible variables on the bulky of the scope:
        if clean_implicit:
            print('  \t+ Filling parameters attribute.')
            scope = fill_parameters(scope)
            print('  \t+ Filling dimensions attribute.')
            scope = fill_dimensions(scope)
            print('  \t+ Filling bulky_var attribute.\n')
            scope = fill_bulky_var(scope)

    return scopes


def fill_module(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.module = SimpleNamespace with imported variables via
    'use' statements:
    E.g.: 'use ghostatom, only: newghostype, nghostcent'

    :param scope: Scope whose attribute scope.module needs to be filled-in.

    :return: the same entry scope with scope.module attribute populated.
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


def fill_parameters(scope: SimpleNamespace) -> SimpleNamespace:
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
    bulky_parameters = []   # parameters found per line.
    for sd in scope.data:
        if sd[0].lower() == "parameter":
            sd_strip = []   # a copy of sd without ending lines.
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


def fill_dimensions(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.dimension = List[SimpleNamespace] with variables
    names and array dimensions.
    E.g.: 'dimension hii(MPARM),sii(MPARM)'

    Args:
        :param scope: Namespace containing the data.

    Returns:
        :return scope: Return the same entry SimpleNamespace with the
                       scope.dimensions attribute populated by a
                       List[SimpleNamespace] containing the variable
                       names and dimensions.
    """
    for sd in scope.data:
        if sd[0] == 'dimension':
            sa = sd[0:1]
            sa += " "
            declaration = separate_dimensions(list_to_string(sd[1:]))
            scope.dimensions.append(declaration)
    return scope


def separate_dimensions(s: str) -> SimpleNamespace:
    """Separate a dimension-string declaration into variables and dimensions.
    The result is stored in a SimpleNamestpace with attributes variables and
    dimensions.
    :param s: Entry string with the dimension declaration.
    :return: SimpleNamespace.variables and SimpleNamespace.dimensions.
    """
    variables, dimensions = [], []
    s_splitted = (s.replace("),", ") ")).split()
    variable = ""
    close_parenethesis = False
    for i in s_splitted:
        if "(" and ")" in i:
            close_parenethesis = True
        elif "(" in i:
            close_parenethesis = False
        elif ")" in i:
            close_parenethesis = True
        variable += i
        if close_parenethesis:
            variable = variable.replace(",", ", ")
            variables.append(variable[:variable.index("(")])
            dimensions.append(variable[variable.index("("):])
            variable = ""
    return SimpleNamespace(variables=variables, dimensions=dimensions)


def list_to_string(entry_list: list) -> str:
    """ Convert list to string.
    :param entry_list:
    "return str:
    """
    str1 = ""
    for element in entry_list:
        str1 += element
    return str1


def fill_bulky_var(scope: SimpleNamespace) -> SimpleNamespace:
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
                      "go", "goto", "include", "format",
                      "\n"]

    # Avoid Fortran keywords that are not variables:
    exclude = ["&", "dimension", "parameter", "if", "endif", "else", "elseif",
               "end", "open", "close", "do", "call", "write", "goto", "enddo",
               "then", "to", "return", "min", "max", "nint", "abs", "float",
               "data", "log", "dlog", "exp", "dexp", "mod", "sign", "int",
               "status", "format", "file", "unit", "read", "save", "rewind",
               "character", "backspace", "common",
               "dfloat", "dsqrt", "dcos", "dsin", "sqrt", "continue",
               "mpi_status_size", "mpi_integer", "mpi_sum", "mpi_max",
               "mpi_comm_world", "mpi_double_precision",
               "\t", "\n"]

    # Initiate booleans to discern quotes:
    in_quotes, double_quote, quoted_one_word = False, False, False
    quoted_sign = ""

    # Exclude all variables imported by the use statements:
    for sm in scope.module:
        for v in sm.var:
            exclude.append(v.name.lower())

    # Exclude variables declared as parameters:
    for sp in scope.parameters:
        exclude.append(sp)

    # Exclude variables declared with dimensions:
    for sd in scope.dimensions:
        for variable in sd.variables:
            exclude.append(variable)

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

            # Exclude lines like "20 format(....)":
            if sd_strip[0].isdigit() and sd_strip[1] == "format":
                continue

            # Start the main loop:
            s_iter = iter(x for x in sd_strip[starting_point:] if len(x))
            for x in s_iter:
                # Skip xxx variables in lines like 'if() call xxx()':
                if x == "call":
                    next(s_iter)
                    next(s_iter)

                # Skip commented text, e.g. " ier = 0  ! nullify error":
                if x == "!":
                    break
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
                                in_quotes, double_quote = False, False
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
                    quoted_one_word, in_quotes = False, False
                    if double_quote:
                        double_quote = False
                    quoted_sign = ""

    # Finish by deleting redundancies:
    scope.bulky_var = (list(dict.fromkeys(flatten_string_list(bulky_var))))
    return scope


def modify_rawdata(rawdata: List[str], scopes: List[SimpleNamespace],
                   clean_use: bool,
                   clean_implicit: bool) -> List[str]:
    """ Modify rawdata input according to scopes and argument flags.

    :param rawdata: List of the bulky content of the read file.

    :param scopes: List of scopes.

    :param clean_use: Boolean to replace or not the implicit real.

    :param clean_implicit: Boolean to replace or not the implicit real.

    :return: rawdata with modifications.
    """
    for index, scope in enumerate(scopes):
        print('  - Modifying rawdata of scope: %s' % scope.name)
        if clean_use:
            # Count the number of var calls per var per module in scope:
            scope = count_var(scope)

            # clean the raw data
            rawdata = clean_raw_data(rawdata, scope)

        # add undeclared variables:
        if clean_implicit:
            if len(scope.bulky_var):
                rawdata = add_undeclared_variables(rawdata, scope, index)
                rawdata = add_use_precision_kinds(rawdata, scope, index)
                rawdata = delete_parameters(rawdata)
                rawdata = delete_dimensions(rawdata)
            else:
                print('      No potential variables found in the scope.')

        print('    ... done!\n')
    return rawdata


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
    Add undeclared variaables of a scope in rawdata.

    :param rawdata: Entry rawdata to add undeclared variables to.

    :param scope: Scope with the undeclared variables.

    :param index: index of scope in the precendent SimpleNamespace.

    :return: Entry rawdata with the new variables declared.
    """
    # List of integers and floats to add:
    new_integers = ['      integer', ' :: ']
    new_floats = ['      real(dp)', ' :: ']

    # Variables to declare:
    new_variables_to_add = []
    new_integer_parameters, new_float_parameters = [], []
    new_integer_dimensions, new_float_dimensions = [], []

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
        if (len(scope.parameters) % 2 == 0):
            for index_sp in range(0, len(scope.parameters), 2):
                if scope.parameters[index_sp][0] in integer_variables:
                    new_integer_parameters.extend([
                        '      integer', ', ', 'parameter', ' :: ',
                        scope.parameters[index_sp], " = ",
                        scope.parameters[index_sp+1],
                        "\n"])
                else:
                    new_float_parameters.extend([
                        '      real(dp)', ', ', 'parameter', ' :: ',
                        scope.parameters[index_sp], " = ",
                        scope.parameters[index_sp+1],
                        "\n"])
        else:
            print("\n     WARNING --- parameter declaration not resolved")
            print("            is there any special character (*, +, / ..)? \n")

    # Add variables with declared dimensions:
    if len(scope.dimensions):
        for sd in scope.dimensions:
            for variable_index, variable in enumerate(sd.variables):
                if variable[0] in integer_variables:
                    new_integer_dimensions.extend([
                        '      integer', ', ',
                        'dimension', sd.dimensions[variable_index], ' :: ',
                        sd.variables[variable_index], "\n"])
                else:
                    new_float_dimensions.extend([
                        '      real(dp)', ', ',
                        'dimension', sd.dimensions[variable_index], ' :: ',
                        sd.variables[variable_index], "\n"])

    # Add final new line and combine:
    new_integers.append("\n")
    new_floats.append("\n")
    new_variables_to_add = new_integers + new_floats \
                                        + new_float_parameters \
                                        + new_integer_parameters \
                                        + new_integer_dimensions \
                                        + new_float_dimensions

    # Add declared missed variables to raw data after an "implicit none"
    # declaration:
    implicit_indexes = list_duplicates(rawdata, "implicit none")
    rawdata[implicit_indexes[index]+1:
            implicit_indexes[index]] = new_variables_to_add

    # For future references, add new_variables_to_add to scope after
    # the last 'use':
    insert_index = 0
    for sd_index, sd in enumerate(scope.data):
        if sd[0] == 'use':
            insert_index = sd_index
    # If there is not any 'use' statement, insert before a 'implicit':
    if insert_index == 0:
        for sd_index, sd in enumerate(scope.data):
            if sd[0] == 'implicit':
                insert_index = sd_index

    scope.data.insert(insert_index, new_variables_to_add)
    return rawdata


def add_use_precision_kinds(rawdata: List[str],
                            scope: SimpleNamespace, index: int) -> List[str]:
    """
    Add 'use precision_kinds, only: dp' to rawdata and scope if a 'real(dp)'
    declaration is found in scope.

    :param rawdata: Entry rawdata.

    :param scope: Scope to be queried.

    :param index: index of scope in the precendent SimpleNamespace.

    :return: Entry rawdata with the 'use precision_kinds' statement inserted.
    """
    new_floats = False  # True if a real(dp) is declared.
    precision_kinds = False  # True if a 'use precision_kinds' is declared.

    # Get indexes:
    implicit_indexes = list_duplicates(rawdata, "implicit none")

    # Discern if the addition is needed:
    for sm in scope.data:
        if "real(dp)" in [x.lstrip() for x in sm]:
            new_floats = True
    for sm in scope.module:
        if 'precision_kinds' in sm.name:
            precision_kinds = True

    # Add statement to rawdata:
    if new_floats and not precision_kinds:
        use_statement = ["      use precision_kinds, only: dp\n"]
        rawdata[implicit_indexes[index]:
                implicit_indexes[index]] = use_statement

    return rawdata


def list_duplicates(seq: list, item: str):
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


def delete_parameters(rawdata: List[str]) -> List[str]:
    """Delete lines starting with the word parameter, e.g:
       parameter(zero =0.d0, one=1.0d0)

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    rawdata = [rd for rd in rawdata if not(
               rd.lstrip(" ").startswith("parameter")
               and len(rd.lstrip(" ")) > 9)]

    return rawdata


def delete_dimensions(rawdata: List[str]) -> List[str]:
    """Delete lines starting with the word dimensions, e.g:
       dimension r(3),r_basis(3) 

    Args:
        rawdata (List[str]): [description]

    Returns:
        List[List[str]]: [description]
    """
    rawdata = [rd for rd in rawdata if not(
               rd.lstrip(" ").startswith("dimension")
               and len(rd.lstrip(" ")) > 9)]

    return rawdata
