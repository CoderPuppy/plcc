import argparse
import dataclasses
import os
import re
import shutil
import typing

from myplcc.lexer import Terminal, Terminals
from myplcc.project import Project
from myplcc.grammar import RuleItem, GrammarRule, NonTerminal, compute_tables
import myplcc.parse as parse
from myplcc.compat.commands import Scan, Parser, Rep

# TODO
#   compat
#       old extra code placeholders
#   errors
#       parse errors
#   fancy CFGs
#       quantifiers
#       repeating nonempty
#       repeating antiseparator
#       repeating fancy separator
#   build system
#   extends, implements
#   nested classes
#   crosspackage grammar

# incompatibilities
#   Scan.match - the second argument is myplcc.ITrace, not Trace
#   new Parser(BufferedReader) - missing
#   Parser.scn - missing
#   Parser.parse - private, takes myplcc.Scan and myplcc.ITrace
#   Scan !<: IScan
#   IScan, ILazy, IMatch - missing
#   Trace, ITrace - missing
#   <grammar>.parse - take myplcc.Scan, myplcc.ITrace instead of Scan and Trace

parser = argparse.ArgumentParser(
    description='Generate a language from a .plcc file',
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument('files',
    action='append',
    type=str,
    help='The .plcc files to process'
)
parser.add_argument('-o', '--output', dest = 'output_dir',
    action='store',
    type=str,
    default=os.path.join(os.getcwd(), 'Java'),
    help='The directory to output the generated .java files',
)
parser.add_argument('--clear-output', dest='clear_output',
    action=argparse.BooleanOptionalAction,
    default=False,
    help='Clear the output directory',
)
class OptionAction(argparse.Action):
    def __init__(self, option_strings, dest, default, type,
        help=None, metavar=None, required=False):
        assert type.__origin__ is typing.Union
        choices = []
        for t in type.__args__:
            if t is None.__class__:
                choices.append('none')
            elif t.__origin__ is typing.Literal:
                choices.append(t.__args__[0])
            else:
                raise RuntimeError('bad option choice: {}'.format(t))
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            type=str,
            help=help,
            metavar=metavar,
            required=required,
            nargs=1,
            choices=choices,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        choice = values[0]
        if choice == 'none':
            choice = None
        setattr(namespace, self.dest, choice)
for field in dataclasses.fields(parse.State):
    if 'option' in field.metadata:
        name = re.sub(r'_', r'-', field.name)
        if field.type == bool:
            parser.add_argument(
                '--{}'.format(name),
                dest=field.name,
                action=argparse.BooleanOptionalAction,
                type=bool,
                default=field.default,
                help=field.metadata['option'],
            )
            continue

        if field.type.__origin__ is typing.Union:
            parser.add_argument(
                '--{}'.format(name),
                dest=field.name,
                action=OptionAction,
                type=field.type,
                default=field.default,
                help=field.metadata['option'],
            )
            continue

        raise RuntimeError('bad option type: {}'.format(field.type))
args = parser.parse_args()

proj = Project()

base_state = parse.State(
    project = proj,
    fname = None,
    debug_parser = args.debug_parser,
    compat_terminals = args.compat_terminals,
    compat_extra_imports = args.compat_extra_imports,
    compat_auto_scan = args.compat_auto_scan,
    compat_auto_parser = args.compat_auto_parser,
    compat_auto_rep = args.compat_auto_rep,
    process_extra_code = args.process_extra_code,
    auto_tostring = args.auto_tostring,
    auto_visitor = args.auto_visitor,
)

for fname in args.files:
    state = dataclasses.replace(base_state,
        fname = fname
    )
    parse.parse(state)
    # TODO: should this check if there is a Scan/Parser/Rep first?
    if state.compat_auto_scan:
        proj.add(state.package_prefix() + 'Scan', Scan(state.terminals))
    try:
        # TODO: this is a bit hacky
        start_nt = next(cls.special for cls in proj.classes.values() if isinstance(cls.special, NonTerminal))
        if state.compat_auto_parser:
            proj.add(state.package_prefix() + 'Parser', Parser(start_nt))
        if state.compat_auto_rep:
            proj.add(state.package_prefix() + 'Rep', Rep(start_nt))
    except StopIteration:
        # no NonTerminals, can't generate Parser or Rep
        pass

compute_tables(proj)
output_dir = os.path.normpath(os.path.join(os.getcwd(), args.output_dir))
try:
    os.mkdir(output_dir)
except FileExistsError:
    pass
if args.clear_output:
    for entry in os.scandir(output_dir):
        if entry.is_dir():
            shutil.rmtree(entry.path)
        else:
            os.remove(entry.path)
proj.generate_code(output_dir)
