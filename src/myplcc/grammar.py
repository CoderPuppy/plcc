from dataclasses import dataclass, field
from typing import Union, Optional, List, Set, Literal, Tuple, Iterable, Callable

from myplcc.lexer import Terminal, Terminals
from myplcc.project import GeneratedClass

def generate_quantified(*,
    indent: str,
    terminals: Terminals,
    first_set: Set[Terminal],
    quantified_min: int,
    quantified_max: Optional[int],
    explicit_rep: bool = False,
    gen: Callable[[str, Optional[str], Optional[str]], Iterable[str]],
    var_suffix: str = '',
):
    def gen_switch(indent, match, done):
        yield '{}t$ = scan$.getCurrentToken();'.format(indent, terminals.terminal_type())
        yield '{}switch(t$.terminal) {{'.format(indent)
        for first in first_set:
            yield '{}\tcase {}:'.format(indent, first.name)
        yield from match(indent + '\t\t')
        yield '{}\tdefault:'.format(indent)
        yield from done(indent + '\t\t')
        yield '{}}}'.format(indent)

    yield '{}int count{} = 0;'.format(indent, var_suffix)
    if explicit_rep:
        yield '{}boolean needMore{};'.format(indent, var_suffix)
        yield from gen_switch(indent,
            match = lambda indent: [
                '{}needMore{} = true;'.format(indent, var_suffix),
                '{}break;'.format(indent),
            ],
            done = lambda indent: [
                '{}needMore = false;'.format(indent, var_suffix),
                '{}break;'.format(indent),
            ]
        )
        yield '{}while(needMore{}) {{'.format(indent, var_suffix)
    else:
        yield '{}LOOP{}:'.format(indent, var_suffix)
        if quantified_max:
            yield '{}while(count{} < {}) {{'.format(indent, quantified_max, var_suffix)
        else:
            yield '{}while(true) {{'.format(indent)
        match = lambda indent: [indent + 'break;']
        done = lambda indent: ['{}break LOOP{};'.format(indent, var_suffix)]
        if quantified_min == 0:
            yield from gen_switch(indent + '\t', match, done)
        else:
            yield '{}\tif(count{} >= {}) {{'.format(indent, var_suffix, quantified_min)
            yield from gen_switch(indent + '\t\t', match, done)
            yield '{}\t}}'.format(indent)
    yield '{}\tcount{} += 1;'.format(indent, var_suffix)
    yield from gen(
        indent + '\t',
        'count{} < {}'.format(var_suffix, quantified_min) if quantified_min > 1 else None,
        'count{} < {}'.format(var_suffix, quantified_max) if quantified_max else None,
    )
    yield '{}}}'.format(indent)

@dataclass(eq = False)
class RuleItem:
    symbol: Union[Terminal, 'NonTerminal']
    field: Optional[str]
    quantifier: Optional[Tuple[int, Optional[int]]] = field(default=None)

    def field_name(self, rule):
        if self.field is None:
            return None
        elif rule.is_repeating:
            return self.field + 'List'
        else:
            return self.field
    def symbol_typ(self, rule):
        if isinstance(self.symbol, Terminal):
            return rule.nonterminal.terminals.token_type()
        else:
            return self.symbol.generated_class.class_name
    def single_typ(self, rule):
        typ = self.symbol_typ(rule)
        if self.quantifier:
            return 'List<{}>'.format(typ)
        else:
            return typ
    def field_typ(self, rule):
        typ = self.single_typ(rule)
        if rule.is_repeating:
            return 'List<{}>'.format(typ)
        else:
            return typ
    def generate_tostring(self, rule, access_post):
        if self.field:
            if rule.generate_tostring == 'exact' or isinstance(self.symbol, NonTerminal):
                convert_post = 'toString()'
            else:
                convert_post = 'str'
            return 'this.{}{}.{}'.format(self.field, access_post, convert_post)
        else:
            if rule.generate_tostring == 'approx' and isinstance(self.symbol, Terminal):
                s = self.symbol.approx_example()
            else:
                s = self.symbol.name
            return '"{}"'.format(s)

@dataclass(eq = False)
class GrammarRule:
    nonterminal: 'NonTerminal'
    generated_class: Optional[GeneratedClass] = field(init=False, default=None)
    is_repeating: bool
    separator: Optional[Terminal]
    src_file: str
    src_line: int
    items: List[RuleItem] = field(default_factory=list)
    first_set: Optional[Set[Terminal]] = field(default=None)
    possibly_empty: Optional[bool] = field(default=None)
    generate_tostring: Union[None, Literal['exact'], Literal['approx']] = field(default=None)
    compat_extra_imports: bool = field(default=False)

    def _generate_fields(self):
        params = []
        args = []
        inits = []
        if self.is_repeating:
            params.append('int count')
            args.append('count')
            inits.append('\t\tthis.count = count;')
            yield '\tpublic int count;'
        for item in self.items:
            name = item.field_name(self)
            if name is None:
                continue
            typ = item.field_typ(self)
            yield '\tpublic {} {};'.format(typ, name)
            params.append('{} {}'.format(typ, name))
            args.append(name)
            inits.append('\t\tthis.{name} = {name};'.format(name = name))
        yield '\tpublic {}({}) {{'.format(self.generated_class.class_name, ', '.join(params))
        yield from inits
        yield '\t}'
        return args

    def _generate_parse_core(self, indent):
        terminals = self.nonterminal.terminals
        quantified_i = 0
        for item in self.items:
            if isinstance(item.symbol, Terminal):
                parse = terminals.convert_token('scan$.match({}.{}, trace$)'.format(
                    terminals.terminal_type(), item.symbol.name))
                first_set = {item.symbol}
            else:
                parse = '{}.parse(scan$, trace$)'.format(item.symbol_typ(self))
                first_set = item.symbol.first_set

            if item.quantifier:
                quantified_i += 1
                if item.field:
                    yield '{}List<{t}> {} = new ArrayList<{t}>();'.format(
                        indent, item.field,
                        item.symbol_typ(self)
                    )
                    yield '{}{f}List.add({f});'.format(indent, f = item.field)
                    parse = '{}.add({})'.format(item.field, parse)
                yield from generate_quantified(
                    indent = indent,
                    terminals = terminals,
                    first_set = first_set,
                    quantified_min = item.quantifier[0],
                    quantified_max = item.quantifier[1],
                    gen = lambda indent, need_more, allow_more: ['{}{};'.format(indent, parse)],
                    var_suffix = str(quantified_i)
                )
            else:
                if item.field:
                    if self.is_repeating:
                        parse = '{}List.add({})'.format(item.field, parse)
                    else:
                        parse = '{} {} = {}'.format(item.single_typ(self), item.field, parse)
                yield '{}{};'.format(indent, parse)

    def _generate_parse_rep(self, indent, need_more, allow_more):
        yield from self._generate_parse_core(indent)
        if self.separator:
            if need_more:
                yield '{}needMore = {};'.format(indent, need_more)
            yield '{}needMore {}= scan$.getCurrentToken().terminal == {}.{};'.format(
                indent, '||' if need_more else '',
                self.nonterminal.terminals.terminal_type(), self.separator.name
            )
            if allow_more:
                yield '{}needMore &&= {}'.format(indent, allow_more)
            yield '{}if(needMore)'.format(indent)
            yield '{}\tscan$.match(t$.terminal, trace$);'.format(indent)

    def _generate_parse(self, args):
        class_name = self.generated_class.class_name
        terminals = self.nonterminal.terminals
        yield '\tpublic static {class_name} parse(myplcc.Scan<{terminal_type}> scan$, myplcc.ITrace<{terminal_type}> trace$) {{'.format(
            class_name = class_name,
            terminal_type = terminals.terminal_type()
        )
        yield '\t\tmyplcc.Token<{}> t$;'.format(terminals.terminal_type())
        yield '\t\tif(trace$ != null)'
        yield '\t\t\ttrace$ = trace$.nonterm("<{}>:{}", scan$.getLineNumber());'.format(self.nonterminal.name, class_name)
        if self.is_repeating:
            for item in self.items:
                name = item.field
                if name is None:
                    continue
                typ = item.single_typ(self)
                yield '\t\tList<{}> {}List = new ArrayList<{}>();'.format(typ, name, typ)
            yield from generate_quantified(
                indent = '\t\t',
                terminals = terminals,
                first_set = self.first_set,
                quantified_min = 0,
                quantified_max = None,
                explicit_rep = bool(self.separator),
                gen = self._generate_parse_rep,
            )
        else:
            yield from self._generate_parse_core('')
        yield '\t\treturn new {}({});'.format(class_name, ', '.join(args))
        yield '\t}'

    def _generate_tostring(self):
        yield '\t@Override'
        yield '\tpublic String toString() {'
        if self.generate_tostring == 'exact':
            yield '\t\tString str = "{}[";'.format(self.generated_class.class_name)
        else:
            yield '\t\tString str = "";'
        yield '\t\tString sep = "";'
        if self.is_repeating:
            access_post = 'List.get(i)'
            indent = '\t'
            yield '\t\tfor(int i = 0; i < count; i++) {'
        else:
            access_post = ''
            indent = ''
        yield '\t\t{}str += sep + {};'.format(
            indent,
            ' + " " + '.join(
                item.generate_tostring(self, access_post)
                for item in self.items
            ) if self.items else '""'
        )
        if self.is_repeating:
            if self.separator:
                yield '\t\t\tsep = " {} ";'.format(self.separator.approx_example())
            else:
                yield '\t\t\tsep = " ";'
            yield '\t\t}'
        if self.generate_tostring == 'exact':
            yield '\t\tstr += "]";'
        yield '\t\treturn str;'
        yield '\t}'

    def _generate_visit(self):
        if self.nonterminal.rule == self:
            return
        yield '\t@Override'
        yield '\tpublic <T> T visit({}.Visitor<T> visitor) {{'.format(self.nonterminal.generated_class.class_name)
        yield '\t\treturn visitor.visit{}(this);'.format(self.generated_class.class_name)
        yield '\t}'

    def generate_code(self, subs):
        class_name = self.generated_class.class_name
        if self.generated_class.package:
            yield 'package {};'.format('.'.join(self.generated_class.package))
        yield from subs('top', '')
        if self.is_repeating:
            yield 'import java.util.List;'
            yield 'import java.util.ArrayList;'
        if self.compat_extra_imports:
            yield 'import java.util.*;'
        yield from self.nonterminal.terminals.generated_class.import_(self.generated_class.package)
        # TODO: possibly import the other nonterminals, not necessary right now because all nonterminals are in the same package
        yield from subs('import', '')
        # TODO: extends, implements
        if self.nonterminal.rule == self:
            yield 'public class {} {{'.format(class_name)
        else:
            yield 'public class {} extends {} {{'.format(class_name, self.nonterminal.generated_class.class_name)
        args = yield from self._generate_fields()
        yield ''
        yield from self._generate_parse(args)
        if self.generate_tostring:
            yield ''
            yield from self._generate_tostring()
        if self.nonterminal.generate_visitor:
            yield ''
            yield from self._generate_visit()
        yield from subs(None, '\t')
        yield '}'

@dataclass(eq = False)
class NonTerminal:
    terminals: 'Terminals'
    name: str
    rule: Union[None, GrammarRule, Set[GrammarRule]] = field(default=None)
    generated_class: Optional[GeneratedClass] = field(init=False, default=None)
    default_field: str = field(init=False)
    first_set: Optional[Set[Terminal]] = field(default=None)
    possibly_empty: Optional[bool] = field(default=None)
    generate_visitor: bool = field(default=False)
    compat_extra_imports: bool = field(default=False)

    def __post_init__(self):
        self.default_field = self.name

    def make_class_name(name):
        return name[0].upper() + name[1:]

    def _generate_visitor(self):
        assert isinstance(self.rule, set)
        yield '\tpublic interface Visitor<T> {'
        for rule in self.rule:
            class_name = rule.generated_class.class_name
            yield '\t\tT visit{c}({c} {lc});'.format(
                c = class_name, lc = class_name[0].lower() + class_name[1:])
        yield '\t}'
        yield '\tpublic abstract <T> T visit(Visitor<T> visitor);'

    def generate_code(self, subs):
        if isinstance(self.rule, GrammarRule):
            yield from self.rule.generate_code(subs)
        else:
            if self.generated_class.package:
                yield 'package {};'.format('.'.join(self.generated_class.package))
            yield from subs('top', '')
            if self.compat_extra_imports:
                yield 'import java.util.*;'
            yield from self.terminals.generated_class.import_(self.generated_class.package)
            yield from subs('import', '')
            class_name = self.generated_class.class_name
            yield 'public abstract class {} {{'.format(class_name)
            yield '\tpublic static {class_name} parse(myplcc.Scan<{terminal_type}> scan$, myplcc.ITrace<{terminal_type}> trace$) {{'.format(
                class_name = class_name,
                terminal_type = self.terminals.terminal_type()
            )
            yield '\t\tmyplcc.Token<{}> t$ = scan$.getCurrentToken();'.format(self.terminals.terminal_type())
            yield '\t\tswitch(t$.terminal) {'
            for rule in self.rule:
                for first in rule.first_set:
                    yield '\t\t\tcase {}:'.format(first.name)
                yield '\t\t\t\treturn {}.parse(scan$, trace$);'.format(rule.generated_class.class_name)
            yield '\t\t\tdefault:'
            yield '\t\t\t\tthrow new RuntimeException("{} cannot begin with " + t$);'.format(self.name)
            yield '\t\t}'
            yield '\t}'
            if self.generate_visitor:
                yield ''
                yield from self._generate_visitor()
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
                if item.quantifier and item.quantifier.quantifier_min == 0:
                    if next_possibly_empty:
                        raise RuntimeError('{}:{}: FIRST/FIRST conflict in <{}>:{}: quantified item cannot be possibly empty'.format(
                            special.src_file, special.src_line,
                            special.nonterminal.name, special.generated_class.name
                        ))
                    next_possibly_empty = True
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
            if special.is_repeating:
                if special.separator:
                    if possibly_empty:
                        first_set.add(special.separator)
                else:
                    if possibly_empty:
                        raise RuntimeError('{}:{}: FIRST/FIRST conflict in <{}>:{}: repeating rule cannot be possibly empty'.format(
                            special.src_file, special.src_line,
                            special.nonterminal.name, special.generated_class.name
                        ))
                possibly_empty = True
            special.first_set = first_set
            special.possibly_empty = possibly_empty

        done.add(special)
    for cls in project.classes.values():
        compute_table(cls.special)
