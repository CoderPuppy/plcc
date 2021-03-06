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

# TODO
#   compat
#       old Token ✓
#       extra commands: Scan, Rep, Parser
#       extra imports
#       no auto indent for extra code ✓
#       old extra code placeholders
#       (reverse) better names for things (primarily `Scan.lno`)
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

def generate_extra_code(project, cls):
    def gen(name, indent):
        yield '{}//::PLCC::{}'.format(indent, name if name else '')
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

proj = Project()
proj.compat_terminals = False
proj.compat_extra_code_indent = False
# parse.parse(parse.State(proj, os.path.normpath(os.getcwd() + '/../jeh/Handouts/B_PLCC/numlistv5.plcc')))
parse.parse(parse.State(proj, os.path.normpath(os.getcwd() + '/../V3/V3.plcc')))
compute_tables(proj)
for cls in proj.classes.values():
    gen_extra = generate_extra_code(proj, cls)
    if cls.special:
        gen = cls.special.generate_code(gen_extra)
    else:
        gen = gen_extra(None, '')
    path = 'Java/'
    for part in cls.package:
        path += part + '/'
        os.mkdir(path)
    with open('{}{}.java'.format(path, cls.class_name), 'w') as f:
        for line in gen:
            print(line, file = f)
