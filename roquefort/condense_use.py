from roquefort.scope_utils import separate_scope, fill_scopes
from roquefort.clean_use_and_implicit import split_rawdata, replace_ampersand
from collections import defaultdict


def create_newline(module, values, max_line, min_only_offset):
    if len(values) == 0:
        return f'      use {module}\n'

    newlines = []
    base = f'      use {module}, '
    extra_space = min_only_offset - 1 - len(base)
    base += "".join([" "] * extra_space)
    base += "only: "

    newlines.append(base)

    maxlen = max_line - len(base)
    cur = 0
    for i in range(len(values) + 1):
        if i == len(values):
            newlines[-1] += ",".join(values[cur:])
            continue

        if len(",".join(values[cur:i + 1])) > maxlen:
            newlines[-1] += ",".join(values[cur:i])
            cur = i
            newlines.append(base)

    return '\n'.join(newlines) + '\n'


def condense_use(*, overwrite, filename, max_line_length, min_only_offset,
                 sort, **_):
    """condense_use.

    Parameters
    ----------
    overwrite : bool
        overwrite the current file
    filename :
        filename
    max_line_length :
        max_line_length
        _
    """

    # Read the data file and split it:
    with open(filename, "r") as f:
        rawdata = f.readlines()
    no_amp = replace_ampersand(rawdata)
    splitted = split_rawdata(no_amp)
    scopes = separate_scope(splitted)
    fill_scopes(rawdata, scopes, clean_implicit=False, also_no_only=True)

    for scope in scopes:
        condensed_modules = defaultdict(list)
        min_line = len(rawdata)
        for modul in scope.module:
            condensed_modules[modul.name] += [var.name for var in modul.var]
            min_line = min(modul.iline + scope.istart, min_line)
            rawdata[modul.iline + scope.istart] = ''

        if sort:
            condensed_modules = dict(sorted(condensed_modules.items()))
        for k, v in condensed_modules.items():
            rawdata[min_line] += create_newline(k, v, max_line_length,
                                                min_only_offset)

    if overwrite:
        with open(filename, "w") as f:
            f.write("".join(rawdata))
    else:
        print("".join(rawdata))
