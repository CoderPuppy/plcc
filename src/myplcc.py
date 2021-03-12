from collections import OrderedDict, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Union, Tuple, Set, Optional, Dict, List
import io
import itertools
import os
import re
import sys
import typing

from myplcc.lexer import Terminal, Terminals
from myplcc.project import Project
from myplcc.grammar import RuleItem, GrammarRule, NonTerminal, compute_tables
import myplcc.parse as parse
from myplcc.compat.commands import Scan, Parser, Rep

# TODO
#   compat
#       old Token ✓
#       extra commands: Scan, Rep, Parser ✓
#       extra imports ✓
#       no auto indent for extra code ✓
#       old extra code placeholders
#       (reverse) better names for things (primarily `Scan.lno`) ✓
#   packages and imports
#   errors
#   arbno separator ✓
#   arbno antiseparator
#   quantifiers
#   arbno nonempty
#   fancy CFGs
#   build system
#   split file ✓
#   extends, implements
#   parse rules ✓
#   arbno fancy separator
#   visitor
#   nested classes
#   AST toString
#   nonterminal lookup

# incompatibilities
#   Scan.match - the second argument is myplcc.ITrace, not Trace
#   new Parser(BufferedReader) - missing
#   Parser.scn - missing
#   Parser.parse - private, takes myplcc.Scan and myplcc.ITrace
#   Scan !<: IScan
#   IScan, ILazy, IMatch - missing
#   Trace, ITrace - missing
#   <grammar>.parse - take myplcc.Scan, myplcc.ITrace instead of Scan and Trace

def generate_extra_code(project, cls):
    def gen(name, indent):
        yield '{}//::PLCC::{}'.format(indent, name if name else '')
        if project.process_extra_code:
            for line in itertools.chain(project.extra_code[name], cls.extra_code[name]):
                match = re.match('^(\s*)//::PLCC::(\w+)?$', line)
                if match:
                    yield from gen(match.group(2), indent + match.group(1))
                else:
                    if project.compat_extra_code_indent:
                        yield line
                    else:
                        yield indent + line
    return gen
def generate_code(project, out_path):
    for cls in proj.classes.values():
        gen_extra = generate_extra_code(proj, cls)
        if cls.special:
            gen = cls.special.generate_code(gen_extra)
        else:
            gen = gen_extra(None, '')
        path = os.path.normpath(out_path)
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        for part in cls.package:
            path += '/' + part
            try:
                os.mkdir(path)
            except FileExistsError:
                pass
        path += '/{}.java'.format(cls.class_name)
        with open(path, 'w') as f:
            for line in gen:
                print(line, file = f)

proj = Project(
    # compat_terminals = True,
    # compat_extra_code_indent = False,
    # compat_extra_imports = True,
    process_extra_code = False
)
# fname = '/../jeh/Handouts/B_PLCC/numlistv5.plcc'
fname = '/../V3/V3.plcc'
# fname = '/Examples/test.plcc'
ps = parse.State(
    project = proj,
    fname = os.path.normpath(os.getcwd() + fname),
    debug = proj.debug_parser
)
parse.parse(ps)
if proj.compat_auto_scan:
    proj.add(ps.package_prefix() + 'Scan', Scan(ps.terminals))
try:
    start_nt = next(cls.special for cls in proj.classes.values() if isinstance(cls.special, NonTerminal))
    if proj.compat_auto_parser:
        proj.add(ps.package_prefix() + 'Parser', Parser(start_nt))
    if proj.compat_auto_rep:
        proj.add(ps.package_prefix() + 'Rep', Rep(start_nt))
except StopIteration:
    pass
compute_tables(proj)
generate_code(proj, 'Java')
