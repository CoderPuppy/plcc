from dataclasses import dataclass, field
from typing import Union, Optional, List, Set

from myplcc.lexer import Terminal

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
            return rule.nonterminal.terminals.token_type()
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
    items: List[RuleItem] = field(default_factory=list)
    first_set: Optional[Set[Terminal]] = field(default=None)
    possibly_empty: Optional[bool] = field(default=None)

    def generate_code(self, subs):
        class_name = self.generated_class.class_name
        terminals = self.nonterminal.terminals
        if self.generated_class.package:
            yield 'package {};'.format('.'.join(self.generated_class.package))
        yield from subs('top', '')
        if self.is_arbno:
            yield 'import java.util.ArrayList;'
        if self.generated_class.project.compat_extra_imports:
            yield 'import java.util.*;'
        yield from terminals.generated_class.import_(self.generated_class.package)
        # TODO: possibly import the other nonterminals, not necessary right now because all nonterminals are in the same package
        yield from subs('import', '')
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
        yield '\tpublic static {class_name} parse(myplcc.Scan<{terminal_type}> scn$, myplcc.ITrace<{terminal_type}> trace$) {{'.format(
            class_name = class_name,
            terminal_type = terminals.terminal_type()
        )
        yield '\t\tif(trace$ != null)'
        yield '\t\t\ttrace$ = trace$.nonterm("<{}>:{}", scn$.getLineNumber());'.format(self.nonterminal.name, class_name)
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
            yield '\t\t{}myplcc.Token<{}> t$ = scn$.getCurrentToken();'.format(indent, terminals.terminal_type())
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
                parse = 'scn$.match({}.{}, trace$)'.format(terminals.terminal_type(), item.symbol.name)
                if terminals.compat:
                    # TODO: I wish compat would be limited to just lexer.py
                    parse = 'new {}({})'.format(terminals.token_type(), parse)
            else:
                parse = '{}.parse(scn$, trace$)'.format(item.single_typ(self))

            if item.field:
                if self.is_arbno:
                    parse = '{}List.add({})'.format(item.field, parse)
                else:
                    parse = '{} {} = {}'.format(item.single_typ(self), item.field, parse)
            yield '\t\t{}{};'.format(indent, parse)
        if self.is_arbno:
            if self.separator:
                yield '\t\t\t\tt$ = scn$.getCurrentToken();'
                yield '\t\t\t\tif(t$.terminal != {}.{})'.format(terminals.terminal_type(), self.separator.name)
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
    terminals: 'Terminals'
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
            if self.generated_class.package:
                yield 'package {};'.format('.'.join(self.generated_class.package))
            yield from subs('top', '')
            if self.generated_class.project.compat_extra_imports:
                yield 'import java.util.*;'
            yield from self.terminals.generated_class.import_(self.generated_class.package)
            yield from subs('import', '')
            class_name = self.generated_class.class_name
            yield 'public abstract class {} {{'.format(class_name)
            yield '\tpublic static {class_name} parse(myplcc.Scan<{terminal_type}> scn$, myplcc.ITrace<{terminal_type}> trace$) {{'.format(
                class_name = class_name,
                terminal_type = self.terminals.terminal_type()
            )
            yield '\t\tmyplcc.Token<{}> t$ = scn$.getCurrentToken();'.format(self.terminals.terminal_type())
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

def compute_tables(project):
    visited = dict()
    done = set()
    def compute_table(special, prev = None):
        if special in done:
            return
        if special in visited:
            place = prev
            cycle = [special]
            while place != special:
                cycle.append(place)
                place = visited[place]
            raise RuntimeError('left recursive cycle: ' + ' -> '.join(
                '{}:{}'.format(special.generated_class.name, special.__class__.__name__)
                for special in reversed(cycle)
            ))
        visited[special] = prev

        if isinstance(special, NonTerminal):
            if isinstance(special.rule, set):
                first_set = set()
                possibly_empty = False
                for rule in special.rule:
                    compute_table(rule, special)
                    conflict = first_set.intersection(rule.first_set)
                    if conflict:
                        raise RuntimeError('FIRST/FIRST conflict in <{}>: {}'.format(
                            special.name,
                            ', '.join(terminal.name for terminal in conflict)
                        ))
                    first_set.update(rule.first_set)
                    if rule.possibly_empty:
                        if possibly_empty:
                            raise RuntimeError('FIRST/FIRST conflict in <{}>: multiple possibly empty rules'.format(
                                special.name))
                        else:
                            possibly_empty = True
                special.first_set = first_set
                special.possibly_empty = possibly_empty
            elif special.rule is None:
                if isinstance(prev, GrammarRule):
                    raise RuntimeError('{}:{}: use of undefined nonterminal <{}>'.format(
                        prev.src_file, prev.src_line, special.name))
                else:
                    # this should be visited again later, from a GrammarRule
                    # wait until then, so we can give a better error message
                    del visited[special]
                    return
            else:
                compute_table(special.rule, special)
                special.first_set = special.rule.first_set
                special.possibly_empty = special.rule.possibly_empty
        elif isinstance(special, GrammarRule):
            first_set = set()
            possibly_empty = True
            for item in special.items:
                if isinstance(item.symbol, Terminal):
                    next_first_set = {item.symbol}
                    next_possibly_empty = False
                else:
                    compute_table(item.symbol, special)
                    next_first_set = item.symbol.first_set
                    next_possibly_empty = item.symbol.possibly_empty
                conflict = first_set.intersection(next_first_set)
                if conflict:
                    raise RuntimeError('{}:{}: FIRST/FOLLOW conflict in <{}>:{}: {}'.format(
                        special.src_file, special.src_line,
                        special.nonterminal.name, special.generated_class.name,
                        ', '.join(terminal.name for terminal in conflict)
                    ))
                first_set.update(next_first_set)
                if not next_possibly_empty:
                    possibly_empty = False
                    break
            if special.is_arbno:
                if special.separator:
                    if possibly_empty:
                        first_set.add(special.separator)
                else:
                    if possibly_empty:
                        raise RuntimeError('{}:{}: FIRST/FIRST conflict in <{}>:{}: arbno rule cannot be possibly empty'.format(
                            special.src_file, special.src_line,
                            special.nonterminal.name, special.generated_class.name
                        ))
                possibly_empty = True
            special.first_set = first_set
            special.possibly_empty = possibly_empty

        done.add(special)
    for cls in project.classes.values():
        compute_table(cls.special)
