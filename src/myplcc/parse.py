import os
import re

from myplcc.lexer import Terminals, Terminal
from myplcc.grammar import NonTerminal, GrammarRule, RuleItem

def parse(project, fname, f = None, directory = None, terminals = None):
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
            terminals = project.ensure(name, Terminals, lambda: Terminals()).special
            continue

        match = re.match(r'^\s*(skip\b|token\b|)\s*([A-Z][A-Z\d_]*)\s+(\'[^\']*\'|"[^"]*")\s*(?:#.*)?$', line)
        if match:
            skip = match.group(1) == 'skip'
            name = match.group(2)
            pat = match.group(3)
            if pat[0] == '\'':
                pat = '"' + re.sub(r'([\\"])', r'\\\1', pat[1:-1]) + '"'
            if terminals is None:
                terminals = project.add('Token' if project.compat_terminals else 'Terminals', Terminals(compat = project.compat_terminals)).special
            terminals.add(Terminal(
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
                NonTerminal, lambda: NonTerminal(terminals, name)).special
            rule = GrammarRule(
                nonterminal = nt, is_arbno = is_arbno,
                separator = terminals.terminals[separator] if separator else None,
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
                        symbol = terminals.terminals[symbol_name] # TODO
                    else:
                        symbol = project.ensure(NonTerminal.make_class_name(symbol_name),
                            NonTerminal, lambda: NonTerminal(terminals, symbol_name)).special
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
            parse(project, os.path.normpath(os.path.join(directory, include_fname)), terminals = terminals)
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
