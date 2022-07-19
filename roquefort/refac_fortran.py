#!/usr/bin/env python
"""Parser of arguments."""
from roquefort.clean_common import Refactor
from roquefort.clean_use_and_implicit import clean_statements, move_variable
from pathlib import Path
import argparse
from argparse import RawTextHelpFormatter


def main():
    parser = \
      argparse.ArgumentParser(description=" \"\"\"\n"
                              " Tool for refactoring a Fortran code.\n"
                              " It can delete common blocks or"
                              " clean 'use' or 'implicit real'\n"
                              " statements in a filename, e.g.: \n\n"
                              "   python refac_fortran.py --action"
                              "clean_common -n pars -p /usr/home/champ/\n"
                              "   python refac_fortran.py --action clean_use "
                              "--filename regterg.f90\n"
                              "   python refac_fortran.py --action"
                              "clean_implicit --filename splfit.f -ow\n\n"
                              " \"\"\"\n",
                              formatter_class=RawTextHelpFormatter)

    # Main argument: --action
    parser.add_argument('--action',
                        action='store_true',
                        help="Action to performe: clean_common, clean_use or "
                        "clean_implicit.")

    subpasers = parser.add_subparsers(dest='command')
    # --action flags:
    # 1. --action clean_common subarguments:
    clean_common = subpasers.add_parser('clean_common',
                                        help='Clean common blocks.')
    clean_common.add_argument('-n',
                              '--common_block_name',
                              type=str,
                              help="Common block name.")
    clean_common.add_argument('-p',
                              '--path_to_source',
                              type=str,
                              help="Path to champ.",
                              default=".")

    # 2. --action clean_use subarguments:
    clean_use = \
        subpasers.add_parser(
                   'clean_use', help='Clean variables in use statements.')
    clean_use.add_argument("--filename",
                           type=str,
                           help="Name of the file to clean")
    clean_use.add_argument('-ow',
                           '--overwrite',
                           action='store_true',
                           help='Overwrite the inputfile')

    # 3. --action clean_implicit subarguments:
    clean_implicit = \
        subpasers.add_parser('clean_implicit',
                             help='Clean variables in use statements.')
    clean_implicit.add_argument("--filename",
                                type=str,
                                help="Name of the file to clean")
    clean_implicit.add_argument('-ow',
                                '--overwrite',
                                action='store_true',
                                help='Overwrite the inputfile')

    # 4. --action move_var subarguments:
    clean_implicit = \
        subpasers.add_parser('move_var',
                             help='Move a variable to a new module.')
    clean_implicit.add_argument("--filename",
                                type=str,
                                help="Name of the file to clean")
    clean_implicit.add_argument("--var_name",
                                type=str,
                                help="Name of the variable to move")
    clean_implicit.add_argument("--new_module",
                                type=str,
                                help="Name of the new module")
    clean_implicit.add_argument("--from_module",
                                type=str,
                                help="Name of the old module", default=None)


    clean_implicit.add_argument('-ow',
                                '--overwrite',
                                action='store_true',
                                help='Overwrite the inputfile')

    args = parser.parse_args()

    # Rise errors if arguments are not properly given:
    if args.action and not args.command:
        raise parser.error("\nDefine an --action {clean_common, clean_use,"
                           "clean_implicit}.")
    if not args.action:
        raise parser.error("\nDefine an --action {clean_common, clean_use,"
                           "clean_implicit}.")
    if args.command == 'clean_common':
        if not args.common_block_name:
            raise parser.error("\nDefine a --common_block_name")
    elif args.command == 'clean_use' or args.command == 'clean_implicit':
        if not args.filename:
            raise parser.error("\nDefine a --filename name")

    # Execute program depending on the --action:
    if args.action:
        if args.command == "clean_common":
            rs = Refactor(args.common_block_name, Path(args.path_to_source))
            rs.refactor()
        elif args.command == "clean_use" or args.command == "clean_implicit":
            _ = clean_statements(args)
        elif args.command == 'move_var':
            _ = move_variable(args)


if __name__ == "__main__":
    main()
