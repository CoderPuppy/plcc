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

# TODO
#   compat
#       old Token
#       extra commands: Scan, Rep, Parser
#       extra imports
#       no auto indent for extra code
#       old extra code placeholders
#       (reverse) better names for things
#   packages and imports
#   errors
#   arbno separator
#   arbno antiseparator
#   quantifiers
#   arbno nonempty
#   fancy CFGs
#   build system

@dataclass(eq = False)
class Terminal:
    name: str
    pat: str
    skip: bool
    src_file: str
    src_line: int
    default_field: str = field(init=False)

    def __post_init__(self):
        self.default_field = self.name.lower()

@dataclass(eq = False)
class RuleItem:
    symbol: Union[Terminal, 'NonTerminal']
    field: Optional[str]

    def field_name(self, rule):
        if self.field is None:
            return None
        elif rule.is_arbno:
            return self.field + 'List'
        else:
            return self.field
    def single_typ(self, rule):
        if isinstance(self.symbol, Terminal):
            return 'Token<' + rule.nonterminal.lexer.generated_class.class_name + '>'
        else:
            return self.symbol.generated_class.class_name
    def field_typ(self, rule):
        typ = self.single_typ(rule)
        if rule.is_arbno:
            return 'List<{}>'.format(typ)
        else:
            return typ

@dataclass(eq = False)
class GrammarRule:
    nonterminal: 'NonTerminal'
    generated_class: Optional['GeneratedClass'] = field(init=False, default=None)
    is_arbno: bool
    separator: Optional[Terminal]
    src_file: str
    src_line: int
    items: Sequence[RuleItem] = field(default_factory=list)
    first_set: Optional[Set[Terminal]] = field(default=None)
    possibly_empty: Optional[bool] = field(default=None)

    def generate_code(self, subs):
        yield from subs('top', '')
        if self.is_arbno:
            yield 'import java.util.ArrayList;'
        yield 'import java.util.*;' # TODO: compat only
        yield from subs('import', '')
        # TODO: packages
        # yield 'import {};'.format(self.nonterminal.lexer.generated_class.package_name)
        class_name = self.generated_class.class_name
        lexer_name = self.nonterminal.lexer.generated_class.class_name
        # TODO: extends, implements
        if self.nonterminal.rule == self:
            yield 'public class {} {{'.format(class_name)
        else:
            yield 'public class {} extends {} {{'.format(class_name, self.nonterminal.generated_class.class_name)
        params = []
        args = []
        for item in self.items:
            name = item.field_name(self)
            if name is None:
                continue
            typ = item.field_typ(self)
            yield '\tpublic {} {};'.format(typ, name)
            params.append('{} {}'.format(typ, name))
            args.append(name)
        yield '\tpublic {}({}) {{'.format(class_name, ', '.join(params))
        for item in self.items:
            name = item.field_name(self)
            if name is None:
                continue
            yield '\t\tthis.{name} = {name};'.format(name = name)
        yield '\t}'
        yield '\tpublic static {} parse(Scan<{}> scn$, Trace trace$) {{'.format(class_name, lexer_name)
        yield '\t\tif(trace$ != null)'
        yield '\t\t\ttrace$ = trace$.nonterm("<{}>:{}", scn$.lno);'.format(self.nonterminal.name, class_name)
        if self.is_arbno:
            for item in self.items:
                name = item.field
                if name is None:
                    continue
                typ = item.single_typ(self)
                yield '\t\tList<{}> {}List = new ArrayList<{}>();'.format(typ, name, typ)
            if self.separator:
                indent = ''
            else:
                yield '\t\twhile(true) {'
                indent = '\t'
            yield '\t\t{}Token<{}> t$ = scn$.cur();'.format(indent, lexer_name)
            yield '\t\t{}switch(t$.terminal) {{'.format(indent)
            for first in self.first_set:
                yield '\t\t{}case {}:'.format(indent, first.name)
            if self.separator:
                yield '\t\t\twhile(true) {'
            indent = '\t\t'
        else:
            indent = ''
        for item in self.items:
            if isinstance(item.symbol, Terminal):
                parse = 'scn$.match({}.{}, trace$)'.format(lexer_name, item.symbol.name)
            else:
                parse = '{}.parse(scn$, trace$)'.format(typ)

            if item.field:
                if self.is_arbno:
                    parse = '{}List.add({})'.format(item.field, parse)
                else:
                    parse = '{} {} = {}'.format(item.single_typ(self), item.field, parse)
            yield '\t\t{}{};'.format(indent, parse)
        if self.is_arbno:
            if self.separator:
                yield '\t\t\t\tt$ = scn$.cur();'
                yield '\t\t\t\tif(t$.terminal != {}.{})'.format(lexer_name, self.separator.name)
                yield '\t\t\t\t\tbreak;'
                yield '\t\t\t\tscn$.match(t$.terminal, trace$);'
                yield '\t\t\t}'
                yield '\t\t}'
                yield '\t\treturn new {}({});'.format(class_name, ', '.join(args))
            else:
                yield '\t\t\t\tcontinue;'
                yield '\t\t\tdefault:'
                yield '\t\t\t\treturn new {}({});'.format(class_name, ', '.join(args))
                yield '\t\t\t}'
                yield '\t\t}'
        else:
            yield '\t\treturn new {}({});'.format(class_name, ', '.join(args))
        yield '\t}'
        yield from subs(None, '\t')
        yield '}'

@dataclass(eq = False)
class NonTerminal:
    lexer: 'Lexer'
    name: str
    rule: Union[None, GrammarRule, Set[GrammarRule]] = field(default=None)
    generated_class: Optional['GeneratedClass'] = field(init=False, default=None)
    default_field: str = field(init=False)
    first_set: Optional[Set[Terminal]] = field(default=None)
    possibly_empty: Optional[bool] = field(default=None)

    def __post_init__(self):
        self.default_field = self.name

    def make_class_name(name):
        return name[0].upper() + name[1:]

    def generate_code(self, subs):
        if isinstance(self.rule, GrammarRule):
            yield from self.rule.generate_code(subs)
        else:
            yield from subs('top', '')
            yield 'import java.util.*;' # TODO: compat only
            yield from subs('import', '')
            # TODO: packages
            # yield 'import {};'.format(self.lexer.generated_class.package_name)
            class_name = self.generated_class.class_name
            lexer_name = self.lexer.generated_class.class_name
            yield 'public abstract class {} {{'.format(class_name)
            yield '\tpublic static {} parse(Scan<{}> scn$, Trace trace$) {{'.format(class_name, lexer_name)
            yield '\t\tToken<{}> t$ = scn$.cur();'.format(lexer_name)
            yield '\t\tswitch(t$.terminal) {'
            for rule in self.rule:
                for first in rule.first_set:
                    yield '\t\tcase {}:'.format(first.name)
                yield '\t\t\treturn {}.parse(scn$, trace$);'.format(rule.generated_class.class_name)
            yield '\t\tdefault:'
            yield '\t\t\tthrow new RuntimeException("{} cannot begin with " + t$);'.format(self.name)
            yield '\t\t}'
            yield '\t}'
            yield from subs(None, '\t')
            yield '}'

@dataclass(eq = False)
class Lexer:
    generated_class: Optional['GeneratedClass'] = field(init=False, default=None)
    terminals: typing.OrderedDict[str, Terminal] = field(default_factory=OrderedDict)

    def add(self, terminal: Terminal):
        if terminal.name in self.terminals:
            raise RuntimeError('TODO: duplicate terminal: ' + terminal.name)
        self.terminals[terminal.name] = terminal

    def generate_code(self, subs):
        yield from subs('top', '')
        yield from subs('import', '')
        yield 'import java.util.regex.Pattern;'
        # TODO: packages
        class_name = self.generated_class.class_name
        yield 'public enum {} implements ITerminal {{'.format(class_name)
        terminals = list(self.terminals.values())
        for terminal in terminals[:-1]:
            yield '\t{}({}{}),'.format(terminal.name, terminal.pat, ', true' if terminal.skip else '')
        if terminals:
            terminal = terminals[-1]
            yield '\t{}({}{});'.format(terminal.name, terminal.pat, ', true' if terminal.skip else '')
        yield ''
        yield '\tpublic String pattern;'
        yield '\tpublic boolean skip;'
        yield '\tpublic Pattern cPattern;'
        yield ''
        yield '\t{}(String pattern) {{'.format(class_name)
        yield '\t\tthis(pattern, false);'
        yield '\t}'
        yield '\t{}(String pattern, boolean skip) {{'.format(class_name)
        yield '\t\tthis.pattern = pattern;'
        yield '\t\tthis.skip = skip;'
        yield '\t\tthis.cPattern = Pattern.compile(pattern, Pattern.DOTALL);'
        yield '\t}'
        yield from subs(None, '\t')
        yield '}'

@dataclass(eq = False)
class GeneratedClass:
    name: str
    package_name: str
    class_name: str
    special: Optional[object] = field(default=None)
    extra_code: Dict[Optional[str], List[str]] = field(default_factory=lambda: defaultdict(lambda: list()))

@dataclass(eq = False)
class Project:
    classes: Dict[str, GeneratedClass] = field(default_factory=dict)
    extra_code: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(lambda: list()))

    def add(self, name, special = None):
        if name in self.classes:
            raise RuntimeError('TODO: duplicate class: ' + class_name)
        parts = name.split('.')
        package_name = '.'.join(parts[:-1])
        class_name = parts[-1]
        cls = GeneratedClass(name, package_name, class_name, special)
        if special is not None:
            special.generated_class = cls
        self.classes[class_name] = cls
        return cls

    def ensure(self, name, typ, make):
        if name in self.classes:
            cls = self.classes[name]
            assert isinstance(cls.special, typ) # TODO
            return cls
        else:
            return self.add(name, special = make())

def process(project, fname, f = None, directory = None, lexer = None):
    if f is None:
        f = open(fname, 'r')
    if directory is None:
        directory = os.path.dirname(fname)
    line_num = 0
    for line in f:
        line_num += 1

        match = re.match(r'^\s*terminals\s+(\w+)\s*(?:#.*)?$', line)
        if match:
            name = match.group(1)
            lexer = project.ensure(name, Lexer, lambda: Lexer()).special
            continue

        match = re.match(r'^\s*(skip\b|token\b|)\s*([A-Z][A-Z\d_]*)\s+(\'[^\']*\'|"[^"]*")\s*(?:#.*)?$', line)
        if match:
            skip = match.group(1) == 'skip'
            name = match.group(2)
            pat = match.group(3)
            if pat[0] == '\'':
                pat = '"' + re.sub(r'([\\"])', r'\\\1', pat[1:-1]) + '"'
            if lexer is None:
                lexer = project.add('Terminals', Lexer()).special
            lexer.add(Terminal(
                name, pat, skip,
                src_file = fname, src_line = line_num
            ))
            continue

        match = re.match(r'^\s*<([a-z]\w*)>(?::([A-Z][\$\w]*))?\s*(::|\*\*)=(.*?)(?:\s+\+([A-Z][A-Z_\d]*))?\s*(?:#.*)?$', line)
        if match:
            name = match.group(1)
            subclass = match.group(2)
            is_arbno = match.group(3) == '**'
            body = match.group(4)
            separator = match.group(5)
            nt = project.ensure(NonTerminal.make_class_name(name),
                NonTerminal, lambda: NonTerminal(lexer, name)).special
            rule = GrammarRule(
                nonterminal = nt, is_arbno = is_arbno,
                separator = lexer.terminals[separator] if separator else None,
                src_file = fname, src_line = line_num
            )
            if separator is not None:
                assert is_arbno # TODO
            if subclass:
                if nt.rule is None:
                    nt.rule = set()
                else:
                    assert isinstance(nt.rule, set) # TODO
                nt.rule.add(rule)
                project.add(subclass, rule)
            else:
                assert nt.rule is None # TODO
                nt.rule = rule
                rule.generated_class = nt.generated_class
            for item in re.split(r'\s+', body):
                if item == '':
                    continue
                # TODO: maybe -FOO only matches FOO on the last run
                match = re.match(r'^(<)?(?:([a-z]\w*)|([A-Z][A-Z_\d]*))(?(1)>)((?!\d)\w+)?$', item)
                if match:
                    is_captured = match.group(1) is not None
                    terminal = match.group(2) is None
                    symbol_name = match.group(2) or match.group(3)
                    field = match.group(4)
                    if terminal:
                        symbol = lexer.terminals[symbol_name] # TODO
                    else:
                        symbol = project.ensure(NonTerminal.make_class_name(symbol_name),
                            NonTerminal, lambda: NonTerminal(lexer, symbol_name)).special
                    if field is None:
                        field = symbol.default_field
                    if not is_captured:
                        field = None
                    rule.items.append(RuleItem(symbol, field))
                    continue
                raise RuntimeError('TODO: unhandled item: ' + item)
            continue

        match = re.match(r'^\s*include\s+(\S+)\s*(?:#.*)?$', line)
        if match:
            include_fname = match.group(1)
            process(project, os.path.normpath(os.path.join(directory, include_fname)), lexer = lexer)
            continue

        match = re.match(r'^\s*(\w+)(?::(\w+))?\s*(?:#.*)?$', line)
        if match:
            name = match.group(1)
            section = match.group(2)
            cls = project.ensure(name, object, lambda: None)
            code = cls.extra_code[section]
            for line in f:
                line_num += 1

                if re.match(r'^\s*%%%\s*(?:#.*)?$', line):
                    break
                if re.match(r'^\s*%?\s*(?:#.*)?$', line):
                    continue
                raise RuntimeError('TODO')
            for line in f:
                line_num += 1

                if re.match(r'^\s*%%%\s*(?:#.*)?$', line):
                    break

                code.append(line.rstrip())
            continue

        if re.match(r'^\s*%?\s*(?:#.*)?$', line):
            continue

        raise RuntimeError('TODO: unhandled line: ' + line.rstrip())

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
        for line in itertools.chain(project.extra_code[name], cls.extra_code[name]):
            yield indent + line
            match = re.match('^(\s*)//::PLCC::(\w+)?', line)
            if match:
                yield from gen(match.group(2), indent + match.group(1))
    return gen

proj = Project()
process(proj, os.path.normpath(os.getcwd() + '/../jeh/Handouts/B_PLCC/numlistv5.plcc'))
compute_tables(proj)
for cls in proj.classes.values():
    gen_extra = generate_extra_code(proj, cls)
    if cls.special:
        gen = cls.special.generate_code(gen_extra)
    else:
        gen = gen_extra(None, '')
    with open('Java/{}.java'.format(cls.class_name), 'w') as f:
        for line in gen:
            print(line, file = f)
