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
from myplcc.grammar import RuleItem, GrammarRule, NonTerminal
from myplcc.parse import parse

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
#   arbno separator
#   arbno antiseparator
#   quantifiers
#   arbno nonempty
#   fancy CFGs
#   build system
#   split file
#   extends, implements
#   parse rules

def compute_tables(project):
    visited = set()
    done = set()
    def compute_table(cls):
        if cls in done:
            return
        if cls in visited:
            raise RuntimeError('TODO: recursion')
        visited.add(cls)

        if isinstance(cls, NonTerminal):
            if isinstance(cls.rule, set):
                first_set = set()
                possibly_empty = False
                for rule in cls.rule:
                    compute_table(rule)
                    if first_set.intersection(rule.first_set):
                        raise RuntimeError('TODO: FIRST/FIRST conflict: ' + cls.name)
                    first_set.update(rule.first_set)
                    if rule.possibly_empty:
                        if possibly_empty:
                            raise RuntimeError('TODO: FIRST/FIRST conflict: ' + cls.name)
                        else:
                            possibly_empty = True
                cls.first_set = first_set
                cls.possibly_empty = possibly_empty
            else:
                compute_table(cls.rule)
                cls.first_set = cls.rule.first_set
                cls.possibly_empty = cls.rule.possibly_empty
        elif isinstance(cls, GrammarRule):
            first_set = set()
            possibly_empty = True
            for item in cls.items:
                if isinstance(item.symbol, Terminal):
                    next_first_set = {item.symbol}
                    next_possibly_empty = False
                else:
                    compute_table(item.symbol)
                    next_first_set = item.symbol.first_set
                    next_possibly_empty = item.symbol.possibly_empty
                if first_set.intersection(next_first_set):
                    raise RuntimeError('TODO: FIRST/FOLLOW conflict: ' + cls.generated_class.name)
                first_set.update(next_first_set)
                if not next_possibly_empty:
                    possibly_empty = False
                    break
            if cls.is_arbno:
                if cls.separator:
                    if possibly_empty:
                        first_set.add(cls.separator)
                else:
                    assert not possibly_empty # TODO
                possibly_empty = True
            cls.first_set = first_set
            cls.possibly_empty = possibly_empty

        done.add(cls)
    for cls in project.classes.values():
        compute_table(cls.special)

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
parse(proj, os.path.normpath(os.getcwd() + '/../jeh/Handouts/B_PLCC/numlistv5.plcc'))
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
