from dataclasses import dataclass, field, replace
from typing import Optional, Callable, List
import os
import re
import io

from myplcc.lexer import Terminals, Terminal
from myplcc.grammar import NonTerminal, GrammarRule, RuleItem
from myplcc.project import Project

@dataclass(eq = False)
class State:
    project: Project
    fname: str
    terminals: Optional[Terminals] = field(default = None)
    f: Optional[io.TextIOBase] = field(default=None) # this should only be None when passed to `parse`
    directory: Optional[str] = field(default=None) # this should only be None when passed to `parse`
    debug: bool = field(default=False)
    line_num: int = field(default=0)
    package: List[str] = field(default_factory=list)

    def package_prefix(self):
        return ''.join(part + '.' for part in self.package)

@dataclass(eq = False)
class Rule:
    pat: re.Pattern
    f: Callable[[State, re.Match], None]

NORMAL = r'^\s*{}\s*(?:#.*)?$'
JAVA_IDENT = r'(?!\d)[\w$_]+'
JAVA_PATH = r'(?:{i}\.)*{i}'.format(i = JAVA_IDENT)
TERMINAL = r'[A-Z][A-Z\d_]*'
NONTERMINAL = r'[a-z]\w*'
def str_pat(quote):
    return r'{q}(?:[^{q}\\]|\\.)*{q}'.format(q = quote)

RULES = []
def rule(pat):
    def add(f):
        rule = Rule(re.compile(NORMAL.format(pat)), f)
        RULES.append(rule)
        return rule
    return add

@rule(r'terminals\s+(\.?{})'.format(JAVA_PATH))
def handle_terminals(state, match):
    name = match.group(1)
    if name[0] == '.':
        name = state.package_prefix() + name[1:]
    state.terminals = project.ensure(name, Terminals, lambda: Terminals()).special

@rule(r'(skip\b|token\b|)\s*({t})\s+({ss}|{ds})'.format(
    t = TERMINAL, ss = str_pat('\''), ds = str_pat('"')
))
def handle_terminal(state, match):
    skip = match.group(1) == 'skip'
    name = match.group(2)
    pat = match.group(3)
    if pat[0] == '\'':
        pat = '"' + re.sub(r'([\\"])', r'\\\1', re.sub(r'\\\'', r'\'', pat[1:-1])) + '"'
    if state.terminals is None:
        # TODO: error handling
        state.terminals = state.project.add(
            state.package_prefix() + ('Token' if state.project.compat_terminals else 'Terminals'),
            Terminals(compat = state.project.compat_terminals)
        ).special
    state.terminals.add(Terminal(
        name, pat, skip,
        src_file = state.fname, src_line = state.line_num
    ))

RULE_ITEM_SPLIT_PAT = re.compile(r'\s+')
RULE_ITEM_PAT = re.compile(r'^(<)?(?:([a-z]\w*)|([A-Z][A-Z_\d]*))(?(1)>)((?!\d)\w+)?$')
@rule(r'<({nt})>(?::({ji}))?\s*(::|\*\*)=(.*?)(?:\s+\+({t}))?'.format(
    nt = NONTERMINAL, ji = JAVA_IDENT, t = TERMINAL
))
def handle_grammar_rule(state, match):
    name = match.group(1)
    subclass = match.group(2)
    is_repeating = match.group(3) == '**'
    body = match.group(4)
    separator = match.group(5)
    nt = state.project.ensure(
        state.package_prefix() + NonTerminal.make_class_name(name),
        NonTerminal, lambda: NonTerminal(state.terminals, name)
    ).special
    rule = GrammarRule(
        nonterminal = nt, is_repeating = is_repeating,
        separator = state.terminals.terminals[separator] if separator else None,
        src_file = state.fname, src_line = state.line_num
    )
    if separator is not None and not is_repeating:
        raise RuntimeError('{}:{}: separator in non-repeating rule <{}>{}'.format(
            state.fname, state.line_num,
            name, ':' + subclass if subclass else ''
        ))
    if subclass:
        if nt.rule is None:
            nt.rule = set()
        elif not isinstance(nt.rule, set):
            raise RuntimeError('{}:{}: defining a subclass rule for nonterminal <{}> previously defined at {}:{}'.format(
                state.fname, state.line_num,
                name, nt.rule.src_file, nt.rule.src_line
            ))
        nt.rule.add(rule)
        # TODO: error handling
        state.project.add(state.package_prefix() + subclass, rule)
    else:
        if nt.rule is not None:
            prev_rule = nt.rule if isinstance(nt.rule, GrammarRule) else next(nt.rule)
            raise RuntimeError('{}:{}: defining a rule for nonterminal <{}> previously defined at {}:{}'.format(
                state.fname, state.line_num,
                name, prev_rule.src_file, prev_rule.src_line
            ))
        nt.rule = rule
        rule.generated_class = nt.generated_class
    for item in RULE_ITEM_SPLIT_PAT.split(body):
        if item == '':
            continue
        match = RULE_ITEM_PAT.match(item)
        if match:
            is_captured = match.group(1) is not None
            terminal = match.group(2) is None
            symbol_name = match.group(2) or match.group(3)
            field = match.group(4)
            if terminal:
                try:
                    symbol = state.terminals.terminals[symbol_name] # TODO
                except KeyError as e:
                    raise RuntimeError('{}:{}: unknown terminal: {}'.format(
                        state.fname, state.line_num,
                        symbol_name
                    )) from e
            else:
                # TODO: better way of looking up nonterminals
                symbol = state.project.ensure(
                    state.package_prefix() + NonTerminal.make_class_name(symbol_name),
                    NonTerminal, lambda: NonTerminal(state.terminals, symbol_name)
                ).special
            if field is None:
                field = symbol.default_field
            if not is_captured:
                field = None
            rule.items.append(RuleItem(symbol, field))
            continue
        raise RuntimeError('{}:{}: unhandled item: {}'.format(
            state.fname, state.line_num, item))

@rule(r'include\s+([^\s#]+)')
def handle_include(state, match):
    include_fname = match.group(1)
    parse(replace(state,
        fname = os.path.normpath(os.path.join(state.directory, include_fname)),
        f = None, directory = None, line_num = 0
    ))

EXTRA_CODE_BOUNDARY_PAT = re.compile(NORMAL.format(r'%%%'))
@rule(r'(\*|\.?{jp})(?::(\w+))?'.format(jp = JAVA_PATH))
def handle_extra_code(state, match):
    name = match.group(1)
    section = match.group(2)
    if name == '*':
        code = state.project.extra_code[section]
    else:
        if name[0] == '.':
            name = state.package_prefix() + name[1:]
        cls = state.project.ensure(name, object, lambda: None)
        code = cls.extra_code[section]
    for line in state.f:
        state.line_num += 1

        if handle_blank.pat.match(line):
            continue
        if EXTRA_CODE_BOUNDARY_PAT.match(line):
            break
        raise RuntimeError('{}:{}: expected a code section'.format(
            state.fname, state.line_num))
    for line in state.f:
        state.line_num += 1

        if EXTRA_CODE_BOUNDARY_PAT.match(line):
            break

        code.append(line.rstrip())

@rule(r'package(?:\s+({jp}))'.format(jp = JAVA_PATH))
def handle_package(state, match):
    package_name = match.group(1)
    if package_name:
        package = package_name.split('.')
    else:
        package = []
    state.package = package

@rule(r'%?')
def handle_blank(state, match):
    pass

def parse(state: State):
    if state.f is None:
        state.f = open(state.fname, 'r')
    if state.directory is None:
        state.directory = os.path.dirname(state.fname)
    for line in state.f:
        state.line_num += 1

        matching = set()
        for rule in RULES:
            match = rule.pat.match(line)
            if match:
                matching.add(rule)
                rule.f(state, match)
                if not state.debug:
                    break
        if len(matching) > 1:
            raise RuntimeError('{}:{}: multiple rules match: {}'.format(
                state.fname, state.line_num,
                ', '.format(rule.f.__name__ for rule in matching)
            ))

        if not matching:
            raise RuntimeError('{}:{}: unhandled line'.format(
                state.fname, state.line_num))
