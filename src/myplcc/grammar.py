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
        yield 'import java.util.*;' # TODO: compat only
        yield from terminals.imports(self.generated_class.package)
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
        yield '\tpublic static {class_name} parse(Scan{generic} scn$, ITrace{generic} trace$) {{'.format(
            class_name = class_name,
            generic = '' if terminals.compat else '<{}>'.format(terminals.terminal_type())
        )
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
            yield '\t\t{}{} t$ = scn$.cur();'.format(indent, terminals.token_type())
            yield '\t\t{}switch(t$.{}) {{'.format(indent, terminals.terminal_field())
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
                yield '\t\t\t\tif(t$.{} != {}.{})'.format(terminals.terminal_field(), terminals.terminal_type(), self.separator.name)
                yield '\t\t\t\t\tbreak;'
                yield '\t\t\t\tscn$.match(t$.{}, trace$);'.format(terminals.terminal_field())
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
            yield 'import java.util.*;' # TODO: compat only
            yield from self.terminals.imports(self.generated_class.package)
            yield from subs('import', '')
            # TODO: packages
            # yield 'import {};'.format(self.terminals.generated_class.package_name)
            class_name = self.generated_class.class_name
            yield 'public abstract class {} {{'.format(class_name)
            # TODO: Scan nonsense
            yield '\tpublic static {class_name} parse(Scan{generic} scn$, ITrace{generic} trace$) {{'.format(
                class_name = class_name,
                generic = '' if self.terminals.compat else '<{}>'.format(self.terminals.terminal_type())
            )
            yield '\t\t{} t$ = scn$.cur();'.format(self.terminals.terminal_type())
            yield '\t\tswitch(t$.{}) {{'.format(self.terminals.terminal_field())
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
