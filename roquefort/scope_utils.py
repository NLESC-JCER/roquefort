""" Utilities to build-up scopes."""
from typing import List
from types import SimpleNamespace
from roquefort.string_utils import (flatten_string_list, has_number,
                                split_string_hard, list_to_string,
                                split_string_medium,
                                split_string_with_parenthesis)
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
    end_keyword = ['end', 'end\n', 'contains', 'contains\n', 'END', 'END\n']

    skip_keyword = ['interface', 'interface\n']
    skip_block = False

    # get the index of start/end scope
    name, idx_start, idx_end = [], [], []
    for i, d in enumerate(data):

        d = [el.strip().lower() for el in d]
        
        if len(d) == 0:
            continue


        if d[0].lower() in skip_keyword:
            skip_block = True

        if skip_block:

            if d[0].lower() in end_keyword:
                if len(d) > 1:
                    if d[1].lower() in skip_keyword:
                        skip_block = False

            continue

        if d[0].lower() in start_keyword:
            idx_start.append(i)
            name.append(d[1].split('(')[0].rstrip('\n'))

        if d[0] in end_keyword:
            
            if len(d) > 1 and d[1] == "if":
                continue
            if len(d) > 1 and d[1].startswith("module"):
                continue
            else:
                idx_end.append(i)


    return [SimpleNamespace(name=name, istart=istart, iend=iend,
                            data=data[istart:iend], module=[
                            ], floats=[],
                            integers=[], characters=[], complexes=[],
                            parameters=[], dimensions=[], bulky_var=[])
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

        print('  - Adding scope: %s \n' % scope.name)
        # Find variables in use statements:
        print('  \t+ Filling module attribute.')
        scope = fill_module(scope)

        # Find possible variables on the bulky of the scope:
        if clean_implicit:
            print('  \t+ Filling floats attribute.')
            scope = fill_floats(scope)
            print('  \t+ Filling integers attribute.')
            scope = fill_integers(scope)
            print('  \t+ Filling characters attribute.')
            scope = fill_characters(scope)
            print('  \t+ Filling complex attribute.')
            scope = fill_complexes(scope)
            print('  \t+ Filling parameters attribute.')
            scope = fill_parameters(scope)
            print('  \t+ Filling dimensions attribute.')
            scope = fill_dimensions(scope)
            print('  \t+ Filling bulky_var attribute.')
            scope = fill_bulky_var(scope)
            print('')

    return scopes


def fill_module(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.module = SimpleNamespace with imported variables via
    'use' statements:
    E.g.: 'use ghostatom, only: newghostype, nghostcent'

    :param scope: Scope whose attribute scope.module needs to be filled-in.

    :return: the same entry scope with scope.module attribute populated.
    """

    for iline, sori in enumerate(scope.data):

        s = [so.strip() for so in sori if len(so.strip())>0]

        if len(s) == 0:
            continue

        if len(s) == 2 and s[0].lower() == "use":
            continue

        print(s)
        if len(s) >= 2:
        
            if s[0].lower() == 'use' and s[2].strip().startswith('only'):

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


def fill_floats(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.floats with reals already declared.

    :param scope: Namespace containing the data.

    :return scope: Return the same SimpleNamespace with the
                   scope.floats attribute populated by a
                   SimpleNamespace with variables declared
                   as real numbers.
    """
    for sd in scope.data:
        if sd[0].lower().startswith("real") or \
           sd[0].lower().startswith("real(dp)") or\
           sd[0].lower().startswith("real(kind=8)"):
            if (sd[1].lower().startswith("dimension") and
                sd[2].lower().startswith("allocatable")) or \
               (sd[1].lower().startswith("allocatable") and
                    sd[2].lower().startswith("save")):
                declaration = separate_dimensions(
                    list_to_string(sd[4:]))
            elif (sd[1].lower().startswith("dimension(:") and
                    sd[3].lower().startswith("allocatable")):
                declaration = separate_dimensions(
                    list_to_string(sd[5:]))
            else:
                declaration = separate_dimensions(
                    list_to_string(sd[1:]))
            scope.floats.append(declaration)
    return scope


def fill_integers(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.integers with integers already declared.

    :param scope: Namespace containing the data.

    :return scope: Return the same SimpleNamespace with the
                   scope.floats attribute populated by a
                   SimpleNamespace with variables declared
                   as real numbers.
    """
    for sd in scope.data:
        if sd[0].lower().startswith("integer"):
            if sd[1].lower().startswith("dimension") and \
               sd[2].lower().startswith("allocatable"):
                declaration = separate_dimensions(
                    list_to_string(sd[4:]))
            else:
                declaration = separate_dimensions(
                    list_to_string(sd[1:]))
            scope.integers.append(declaration)
    return scope


def fill_characters(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.characters with integers already declared.

    :param scope: Namespace containing the data.

    :return scope: Return the same SimpleNamespace with the
                   scope.characters attribute populated by a
                   SimpleNamespace with variables declared
                   as characters.
    """
    for sd in scope.data:
        if sd[0].lower().startswith("character"):
            if sd[1].isdigit():
                declaration = separate_dimensions(
                    list_to_string(sd[2:]))
            else:
                declaration = separate_dimensions(
                    list_to_string(sd[1:]))
            scope.characters.append(declaration)
    return scope


def fill_complexes(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.complexes with complexes already declared.

    :param scope: Namespace containing the data.

    :return scope: Return the same SimpleNamespace with the
                   scope.complexes attribute populated by a
                   SimpleNamespace with variables declared
                   as complex numbers.
    """
    for sd in scope.data:
        if sd[0].lower().startswith("complex") or \
           sd[0].lower().startswith("complex(dp)"):
            if (sd[1].lower().startswith("dimension") and
                sd[2].lower().startswith("allocatable")) or \
               (sd[1].lower().startswith("allocatable") and
                    sd[2].lower().startswith("save")):
                declaration = separate_dimensions(
                    list_to_string(sd[4:]))
            else:
                declaration = separate_dimensions(
                    list_to_string(sd[1:]))
            scope.complexes.append(declaration)
    return scope


def fill_parameters(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.parameters with parameter-declared variables.

    :param scope: Namespace containing the data.

    :return scope: Return the same SimpleNamespace with the
                   scope.parameters attribute populated by a
                   SimpleNamespace containing all the variables
                   declared as parameters.
    """
    for sd in scope.data:
        if sd[0].lower() == "parameter":
            declaration = separate_parameters(list_to_string(sd[1:]))
            scope.parameters.append(declaration)
    return scope


def separate_parameters(s: str) -> SimpleNamespace:
    """Separate a parameters-string line declaration into variables and values.
    The result is stored in a SimpleNamestpace with attributes variables and
    values.

    :param s: Entry string with the dimension declaration.

    :return: SimpleNamespace.variables and SimpleNamespace.values.
    """

    variables, values = [], []

    if "!" in s:  # Avoid ! comments at the end of the line.
        s = s[:s.index("!")]
    s_splitted = (s[1:].replace("\n", ""))[:-1].split(",")

    for i in s_splitted:

        variables.append(i.split("=")[0])
        values.append(i.split("=")[1])
    return SimpleNamespace(variables=variables, values=values)


def fill_dimensions(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Populate scope.dimension = List[SimpleNamespace] of a scope
    with variables names and array dimensions.

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
            declaration = separate_dimensions(list_to_string(sd[1:]))
            scope.dimensions.append(declaration)
    return scope


def separate_dimensions(s: str) -> SimpleNamespace:
    """Separate a dimension-string line into variables and dimensions.
    The result is stored in a SimpleNamestpace with attributes variables and
    dimensions.

    :param s: Entry string with the dimension declaration.

    :return: SimpleNamespace.variables and SimpleNamespace.dimensions.
    """
    variables, dimensions = [], []
    variable = ""
    if "!" in s:  # Avoid ! comments at the end of the line.
        s = s[:s.index("!")]
    if "(" in s:
        s_splitted = split_string_with_parenthesis(s)
        for variable in s_splitted:
            if "(" and ")" in variable:
                variables.append(variable[:variable.index("(")])
                dimensions.append(variable[variable.index("("):])
            else:
                variables.append(variable)
                dimensions.append("None")
    else:
        s_splitted = (s.replace(",", " ")).split()
        for variable in s_splitted:
            variables.append(variable)
            dimensions.append("None")
    return SimpleNamespace(variables=variables, dimensions=dimensions)


def fill_bulky_var(scope: SimpleNamespace) -> SimpleNamespace:
    """
    Filter variables in the bulky scope.data that are not imported by
    the use statements.

    :param scope: Namespace containing the data.

    :return scope: Return the same SimpleNamespace with the
                   scope.bulky_var attribute populated by a simple
                   list[] containing all the unique variables found
                   in scope.data that are not imported by the use imports.
    """
    # Avoid lines with the following starting-words:
    avoid_analysis = ["implicit", "program", "endif", "enddo",
                      "return", "continue", "!", "c", "C", "function", "use",
                      "go", "goto", "include", "format", "integer", "logical",
                      "real*4", "real*8", "real(dp)" "parameter", "dimension",
                      "allocate", "public", "contains",
                      "\n"]

    # Avoid Fortran keywords that are not variables:
    exclude = ["&", "dimension", "parameter", "if", "endif", "else", "elseif",
               "end", "open", "close", "do", "call", "write", "goto", "enddo",
               "then", "to", "return", "min", "max", "nint", "abs", "float",
               "data", "log", "dlog", "exp", "dexp", "mod", "sign", "int",
               "status", "format", "file", "unit", "read", "save", "rewind",
               "character", "backspace", "common", "real", "integer",
               "cmplx", "complex", "complex*16", "only", "while",
               "logical", "form", "allocate", "allocated", "allocatable",
               "deallocate", "dreal", "print", "stop", "subroutine",
               "dfloat", "dsqrt", "dcos", "dsin", "sin", "cos", "sqrt",
               "continue", "mpi_real8", "+", "=", "module",
               "mpi_status_size", "mpi_integer", "mpi_sum", "mpi_max",
               "mpi_comm_world", "mpi_double_precision", "::",
               "\t", "\n"]

    # Avoid some variables or external functions defined by the user:
    user_exclude = ["rannyu", "gauss", "int_from_cart", "gammai", "nterms4",
                    "idiff", "rnorm_nodes_num", "psinl", "psianl",
                    "dpsianl", "psia", "psib", "dpsibnl"]

    # Initiate booleans to discern quotes:
    in_quotes, double_quote, quoted_one_word = False, False, False
    quoted_sign = ""

    # Exclude all variables imported by the use statements:
    exclude.extend(gather_use_variables(scope))

    # Exclude variables already declared as reals:
    for sd in scope.floats:
        exclude.extend(x.lower() for x in sd.variables)

    # Exclude variables already declared as integers:
    for si in scope.integers:
        exclude.extend(x.lower() for x in si.variables)

    # Exclude variables already declared as characters:
    for sc in scope.characters:
        exclude.extend(x.lower() for x in sc.variables)

    # Exclude variables already declared as characters:
    for sc in scope.complexes:
        exclude.extend(x.lower() for x in sc.variables)

    # Exclude variables declared as parameters:
    for sp in scope.parameters:
        exclude.extend(x.lower() for x in sp.variables)

    # Exclude variables declared with dimensions:
    for sd in scope.dimensions:
        exclude.extend(sd.variables)

    # Analyse the whole scope.data:
    bulky_var = []  # carry all the selected variables in scope.data.

    for sd in scope.data:
        # carry the selected variables per scope.data line.
        sd_copy = []
        sd_strip = []   # a copy of sd without ending lines.

        for var in sd:
            sd_strip.append(var.strip("\n").strip("\t").rstrip(","))

        if len(sd_strip) == 0:
            continue

        # Avoid use without only statements:
        if len(sd_strip) == 2 and sd_strip[0] == "use":
            continue

        if len(sd_strip) >= 2:

            if sd_strip[0].lower() in avoid_analysis:
                continue

            # Add variables declared as characters to the exclude list:
            if sd_strip[0].lower() == "character":
                character_var = [
                    x for x in sd_strip[1:] if not x.isdigit()]
                exclude.extend(character_var)

            starting_point = 0

            # Exclude xxx in "subroutine xxx(a, b, c)":
            if sd_strip[0] == "subroutine":
                starting_point = 2

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
            s_iter = iter(
                x for x in sd_strip[starting_point:] if len(x))
            for x in s_iter:
                # Skip xxx variables in lines like 'if() call xxx()':
                if x == "call":
                    next(s_iter)

                # Skip commented text, e.g. " ier = 0  ! nullify error":
                if x == "!":
                    break
                if "!" in x:
                    x = x[:x.index("!")]
                    if not len(x):
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
                # or digit in scientific notation,
                # and has no point or ampersand, etc., and is not a
                # single-quoted word or quoted text:
                is_scientific_number = False
                if has_number(x) and sum(c.isalpha() for c in x) == 1 and \
                   (x.lower()).count('e') == 1:
                    is_scientific_number = True

                if (not x.isdigit()) and \
                   not any(a in x for a in (".", "&", "(",
                                            ")", "\'", "\"")) \
                   and not in_quotes:
                    variable = x
                # Raise waring if the variable is the user_exclude list:
                    if variable in user_exclude:
                        print("\t --- WARNING! ignoring user-defined "
                              "variable: %s" % x)
                        exclude.extend(user_exclude)
                        print("\t --- is it a function? An interface is"
                              "required!")
                # Make sure it has some length, and is not in the
                # exclude list:
                    if len(variable) > 0 and variable.lower() \
                       not in exclude and not is_scientific_number:
                        sd_copy.append(variable)

                # Reset booleans if x is a quoted_one_word:
                if quoted_one_word:
                    quoted_one_word, in_quotes = False, False
                    if double_quote:
                        double_quote = False
                    quoted_sign = ""

            if len(sd_copy):
                bulky_var.append(sd_copy)

    # Finish by deleting redundancies:
    scope.bulky_var = (
        list(dict.fromkeys(flatten_string_list(bulky_var))))
    return scope


def gather_use_variables(scope: SimpleNamespace) -> List[str]:
    """Add to a list all the variables imported by use statements in a
    scope.module.

    :param scope:

    :return: List with the variable names.
    """
    variable_list = []
    for sm in scope.module:
        for v in sm.var:
            variable_list.append(v.name.lower())
    # Quick fix, move somewhere else:
    variable_list.append("mpi_status_size")
    return variable_list


def gather_use_names(scope: SimpleNamespace) -> List[str]:
    """Add to a list all the 'use'-imported modules of scope SimpleNamespace.

    :param scope:

    :return: List with the name of the imported modules via 'use'.
    """
    module_names = []
    for sm in scope.module:
        module_names.append(sm.name.lower())
    return module_names


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
                rawdata = add_undeclared_variables(
                    rawdata, scope, index)
                rawdata = add_use_precision_kinds(
                    rawdata, scope, index)
                rawdata = delete_parameters(rawdata)
                rawdata = delete_dimensions(rawdata)
            else:
                rawdata = add_parameters(rawdata, scope, index)
                rawdata = delete_parameters(rawdata)
                print('      No potential variables found in the scope.')

        print('    ... done!\n')
    return rawdata


def modify_rawdata_move_var(rawdata: List[str], scopes: List[SimpleNamespace],
                   var_name: str,
                   new_module: str) -> List[str]:
    """ Modify rawdata input according to scopes and argument flags.

    :param rawdata: List of the bulky content of the read file.

    :param scopes: List of scopes.

    :param var_name: Name of the new variable.

    :param new_module: name of the new module

    :return: rawdata with modifications.
    """
    insert_lines = []
    for index, scope in enumerate(scopes):
        print('  - Modifying rawdata of scope: %s' % scope.name)
        

        # clean the raw data
        rawdata, isrt_line = remove_variable(rawdata, scope, var_name, new_module)

        if isrt_line is not None:
            insert_lines.append(isrt_line)
        print('    ... done!\n')

    rewrite = False
    for idx, isrt_line in enumerate(insert_lines):
        rewrite = True
        index = idx + isrt_line[0]
        line = isrt_line[1]
        rawdata.insert(index, line)
    return rawdata, rewrite


def count_var(scope: SimpleNamespace) -> SimpleNamespace:
    """[summary]

    Args:
        scope (SimpleNamespace): [description]

    Returns:
        SimpleNamespace: [description]
    """
    # Avoid to count variables in commented lines
    # and in use statements
    exclude = ["c", "C", "!", "use"]
    # data_copy = [var for index, var in enumerate(scope.data)
    #              if var[0] not in exclude]

    # remove commented lines and comment tha
    # are in the middle of the line
    data_copy = []
    for index, var in enumerate(scope.data):
        if var[0] not in exclude:
            idx = [ii for ii, v in enumerate(
                var) if v.startswith('!')]
            if len(idx) > 0:
                data_copy.append(var[:idx[0]])
            else:
                data_copy.append(var)

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
    return len(pattern.findall(joined_data))


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


def remove_variable(rawdata: List[str],
                    scope: SimpleNamespace, var_name: str, new_module: str) -> List[str]:
    """

    Args:
        rawdata (List[str]): [description]
        scope (SimpleNamespace): [description]

    Returns:
        List[str]: [description]
    """


    add_var = False
    for mod in scope.module:

        print('  --  Module : %s' % mod.name)
        nvar = 0
        contains_var = False
        for v in mod.var:
            
            if v.name != var_name:
                nvar += 1
            if v.name == var_name:
                contains_var = True
        
        if contains_var:
        
            idx_rawdata = scope.istart + mod.iline

            if nvar == 0:

                add_var = True
                print('      Only variable %s in module %s, removing the entire module' %(var_name, mod.name))
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
                    
                    if var.name == '!':
                        print(line)
                        line = line[:-2] + ' ! '
                        print(line)

                    elif var.name != var_name:
                        line += var.name + ', '

                    else:
                        add_var = True
                        print('  ---   removing variable %s' % var.name)
                rawdata[idx_rawdata] = line.rstrip(', ') + '\n'

                # remove the unwanted
                idx_rawdata += 1
                while rawdata[idx_rawdata].lstrip(' ').startswith('&'):
                    rawdata[idx_rawdata] = ''
                    idx_rawdata += 1

    # add a new line to the module use 
    insert_line = None
    if add_var:
        print('  --  Adding variable %s to module %s' %
                            (var_name, new_module))
        idx_use = [idx for idx, line in enumerate(rawdata[scope.istart:scope.iend]) if line.lstrip().startswith('use')]
        # new_line = rawdata[idx_use[-1]]
        new_line = '      ' + 'use ' + new_module + ', only: ' + var_name + '\n'
        if len(idx_use)>0:
            offset = idx_use[-1]+1
        else:
            offset = 2
        insert_line = (scope.istart+offset, new_line)
        # rawdata.insert(scope.istart+idx_use[-1]+1, new_line)
    

    return rawdata, insert_line


def add_undeclared_variables(rawdata: List[str],
                             scope: SimpleNamespace, index: int) -> List[str]:
    """
    Add undeclared variables of a scope in rawdata.

    :param rawdata: Entry rawdata to add undeclared variables to.

    :param scope: Scope with the undeclared variables.

    :param index: index of scope in the precendent SimpleNamespace.

    :return: Entry rawdata with the new variables declared.
    """
    # List of integers and floats to add:
    new_integers = ['      integer', ' :: ']
    new_floats = ['      real(dp)', ' :: ']
    new_complexes = ['      complex(dp)', ' :: ']

    # Variables to declare:
    new_variables_to_add = []
    new_integer_parameters, new_float_parameters = [], []
    new_integer_dimensions, new_float_dimensions = [], []

    index_integer = 1
    index_float = 1
    max_line_length = 10  # Here change the maximum of length line.
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
        for sd in scope.parameters:
            for variable_index, variable in enumerate(sd.variables):
                if variable[0] in integer_variables:
                    new_integer_parameters.extend([
                        '      integer', ', ', 'parameter', ' :: ',
                        sd.variables[variable_index], ' = ',
                        sd.values[variable_index], "\n"])
                else:
                    new_float_parameters.extend([
                        '      real(dp)', ', ', 'parameter', ' :: ',
                        sd.variables[variable_index], ' = ',
                        sd.values[variable_index], "\n"])

    # Add variables with declared dimensions:
    if len(scope.dimensions):
        use_variables = gather_use_variables(scope)
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

                # Add the dimension(argument) if it is not in the new_integer
                # list and not in the imported variables by 'use':
                dimension_list = \
                    split_string_medium(sd.dimensions[variable_index])
                dim_stripped = []
                for dl in dimension_list:
                    dim_stripped = split_string_hard(
                        (dl.strip("()")).lower())
                    for ds in dim_stripped:
                        if ds != "*" \
                           and not ds.isdigit() \
                           and ds not in new_integers \
                           and ds not in use_variables:
                            new_integers.extend([", ", ds])

    #  Add the float(dimension_argument) if it is not already declared:
    if len(scope.floats):
        use_variables = gather_use_variables(scope)
        for sf in scope.floats:
            for variable_index, variable in enumerate(sf.variables):
                if sf.dimensions[variable_index] != "None":
                    dimension_list = \
                        split_string_hard(
                            sf.dimensions[variable_index])
                    for dim in dimension_list:
                        dim_stripped = (dim.strip("()")).lower()
                        if dim_stripped != "*" \
                           and not dim_stripped.isdigit() \
                           and dim_stripped not in new_integers \
                           and dim_stripped not in use_variables:
                            new_integers.extend([", ", dim_stripped])

    #  Add the integer(dimension_argument) if it is not already declared:
    if len(scope.integers):
        use_variables = gather_use_variables(scope)
        for sf in scope.integers:
            for variable_index, variable in enumerate(sf.variables):
                if sf.dimensions[variable_index] != "None":
                    dimension_list = \
                        split_string_hard(
                            sf.dimensions[variable_index])
                    for dim in dimension_list:
                        dim_stripped = (dim.strip("()")).lower()
                        if dim_stripped != "*" \
                           and not dim_stripped.isdigit() \
                           and dim_stripped not in new_integers \
                           and dim_stripped not in use_variables:
                            new_integers.extend([", ", dim_stripped])

    #  Add the integer(dimension_argument) if it is not already declared:
    if len(scope.complexes):
        use_variables = gather_use_variables(scope)
        for sf in scope.complexes:
            for variable_index, variable in enumerate(sf.variables):
                if sf.dimensions[variable_index] != "None":
                    dimension_list = \
                        split_string_hard(
                            sf.dimensions[variable_index])
                    for dim in dimension_list:
                        dim_stripped = (dim.strip("()")).lower()
                        if dim_stripped != "*" \
                           and not dim_stripped.isdigit() \
                           and dim_stripped not in new_complexes \
                           and dim_stripped not in use_variables:
                            new_complexes.extend([", ", dim_stripped])

    # Add final new line and combine:
    new_integers.append("\n")
    new_floats.append("\n")
    new_variables_to_add = new_integers + new_integer_dimensions \
                                        + new_integer_parameters \
                                        + new_floats \
                                        + new_float_dimensions \
                                        + new_float_parameters

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
    # True if a 'use precision_kinds' is declared.
    precision_kinds = False

    # Get indexes:
    implicit_indexes = list_duplicates(rawdata, "implicit none")

    # Discern if the addition is needed:
    for sm in scope.data:
        if "real(dp)" in [x.lstrip() for x in sm]:
            new_floats = True
    for sm in scope.module:
        if 'precision_kinds' in sm.name and sm.var[0].name == "dp":
            precision_kinds = True

    # Add statement to rawdata:
    if new_floats and not precision_kinds:
        use_statement = ["      use precision_kinds, only: dp\n"]
        rawdata[implicit_indexes[index]:
                implicit_indexes[index]] = use_statement

    return rawdata


def add_parameters(rawdata: List[str],
                   scope: SimpleNamespace, index: int) -> List[str]:
    """
    Add parmeters in case of a empty bulky_var.

    :param rawdata: Entry rawdata to add undeclared variables to.

    :param scope: Scope with the parameters to add.

    :param index: index of scope in the precendent SimpleNamespace.

    :return: Entry rawdata with the new variables declared.
    """
    if len(scope.parameters):
        new_integer_parameters, new_float_parameters = [], []
        integer_variables = string.ascii_lowercase[8:14]
        for sd in scope.parameters:
            for variable_index, variable in enumerate(sd.variables):
                if variable[0] in integer_variables:
                    new_integer_parameters.extend([
                        '      integer', ', ', 'parameter', ' :: ',
                        sd.variables[variable_index], ' = ',
                        sd.values[variable_index], "\n"])
                else:
                    new_float_parameters.extend([
                        '      real(dp)', ', ', 'parameter', ' :: ',
                        sd.variables[variable_index], ' = ',
                        sd.values[variable_index], "\n"])

        # Add final new line and combine:
        new_variables_to_add = new_integer_parameters \
            + new_float_parameters

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
    rawdata = [rd for rd in rawdata if not((
               rd.lstrip(" ").startswith("parameter")
               and not rd.lstrip(" ") == "parameters")
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
