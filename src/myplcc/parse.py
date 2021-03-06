from dataclasses import dataclass, field, replace
from typing import Optional, Callable
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

@dataclass(eq = False)
class Rule:
    pat: re.Pattern
    f: Callable[[State, re.Match], None]

RULES = []
def rule(pat):
    def add(f):
        rule = Rule(re.compile(pat), f)
        RULES.append(rule)
        return rule
    return add

@rule(r'^\s*terminals\s+(\w+)\s*(?:#.*)?$')
def handle_terminals(state, match):
    name = match.group(1)
    state.terminals = project.ensure(name, Terminals, lambda: Terminals()).special

@rule(r'^\s*(skip\b|token\b|)\s*([A-Z][A-Z\d_]*)\s+(\'[^\']*\'|"[^"]*")\s*(?:#.*)?$')
def handle_terminal(state, match):
    skip = match.group(1) == 'skip'
    name = match.group(2)
    pat = match.group(3)
    if pat[0] == '\'':
        pat = '"' + re.sub(r'([\\"])', r'\\\1', pat[1:-1]) + '"'
    if state.terminals is None:
        state.terminals = state.project.add(
            'Token' if state.project.compat_terminals else 'Terminals',
            Terminals(compat = state.project.compat_terminals)
        ).special
    state.terminals.add(Terminal(
        name, pat, skip,
        src_file = state.fname, src_line = state.line_num
    ))

@rule(r'^\s*<([a-z]\w*)>(?::([A-Z][\$\w]*))?\s*(::|\*\*)=(.*?)(?:\s+\+([A-Z][A-Z_\d]*))?\s*(?:#.*)?$')
def handle_grammar_rule(state, match):
    name = match.group(1)
    subclass = match.group(2)
    is_arbno = match.group(3) == '**'
    body = match.group(4)
    separator = match.group(5)
    nt = state.project.ensure(NonTerminal.make_class_name(name),
        NonTerminal, lambda: NonTerminal(state.terminals, name)).special
    rule = GrammarRule(
        nonterminal = nt, is_arbno = is_arbno,
        separator = state.terminals.terminals[separator] if separator else None,
        src_file = state.fname, src_line = state.line_num
    )
    if separator is not None:
        assert is_arbno # TODO
    if subclass:
        if nt.rule is None:
            nt.rule = set()
        else:
            assert isinstance(nt.rule, set) # TODO
        nt.rule.add(rule)
        state.project.add(subclass, rule)
    else:
        assert nt.rule is None # TODO
        nt.rule = rule
        rule.generated_class = nt.generated_class
    for item in re.split(r'\s+', body):
        if item == '':
            continue
        # TODO: compile pattern
        match = re.match(r'^(<)?(?:([a-z]\w*)|([A-Z][A-Z_\d]*))(?(1)>)((?!\d)\w+)?$', item)
        if match:
            is_captured = match.group(1) is not None
            terminal = match.group(2) is None
            symbol_name = match.group(2) or match.group(3)
            field = match.group(4)
            if terminal:
                symbol = state.terminals.terminals[symbol_name] # TODO
            else:
                symbol = state.project.ensure(NonTerminal.make_class_name(symbol_name),
                    NonTerminal, lambda: NonTerminal(state.terminals, symbol_name)).special
            if field is None:
                field = symbol.default_field
            if not is_captured:
                field = None
            rule.items.append(RuleItem(symbol, field))
            continue
        raise RuntimeError('TODO: unhandled item: ' + item)

@rule(r'^\s*include\s+(\S+)\s*(?:#.*)?$')
def handle_include(state, match):
    include_fname = match.group(1)
    parse(replace(state,
        fname = os.path.normpath(os.path.join(state.directory, include_fname)),
        f = None, directory = None, line_num = 0
    ))

@rule(r'^\s*(\w+)(?::(\w+))?\s*(?:#.*)?$')
def handle_extra_code(state, match):
    name = match.group(1)
    section = match.group(2)
    if name == '*':
        code = state.project.extra_code[section]
    else:
        cls = state.project.ensure(name, object, lambda: None)
        code = cls.extra_code[section]
    for line in state.f:
        state.line_num += 1

        # TODO: compile these patterns
        if re.match(r'^\s*%%%\s*(?:#.*)?$', line):
            break
        if re.match(r'^\s*%?\s*(?:#.*)?$', line):
            continue
        raise RuntimeError('TODO')
    for line in state.f:
        state.line_num += 1

        if re.match(r'^\s*%%%\s*(?:#.*)?$', line):
            break

        code.append(line.rstrip())

@rule(r'^\s*%?\s*(?:#.*)?$')
def handle_blank(state, match):
    pass

def parse(state: State):
    if state.f is None:
        state.f = open(state.fname, 'r')
    if state.directory is None:
        state.directory = os.path.dirname(state.fname)
    for line in state.f:
        state.line_num += 1

        handled = False
        for rule in RULES:
            match = rule.pat.match(line)
            if match:
                if handled:
                    raise RuntimeError('TODO: multiple rules match line: ' + line.rstrip())
                handled = True
                rule.f(state, match)
                if not state.debug:
                    break

        if not handled:
            raise RuntimeError('TODO: unhandled line: ' + line.rstrip())
