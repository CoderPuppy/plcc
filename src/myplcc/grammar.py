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
        yield '{}switch(scan$.getCurrentToken().terminal) {{'.format(indent)
        for first in first_set:
            yield '{}\tcase {}:'.format(indent, first.name)
        yield from match(indent + '\t\t')
        yield '{}\tdefault:'.format(indent)
        yield from done(indent + '\t\t')
        yield '{}}}'.format(indent)

    yield '{}int count{} = 0;'.format(indent, var_suffix)
    if explicit_rep:
        if quantified_min > 0:
            yield '{}boolean needMore{}$ = true;'.format(indent, var_suffix)
        else:
            yield '{}boolean needMore{}$;'.format(indent, var_suffix)
            yield from gen_switch(indent,
                match = lambda indent: [
                    '{}needMore{}$ = true;'.format(indent, var_suffix),
                    '{}break;'.format(indent),
                ],
                done = lambda indent: [
                    '{}needMore{}$ = false;'.format(indent, var_suffix),
                    '{}break;'.format(indent),
                ]
            )
        yield '{}while(needMore{}$) {{'.format(indent, var_suffix)
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
        'count{} >= {}'.format(var_suffix, quantified_max) if quantified_max else None,
    )
    yield '{}}}'.format(indent)

@dataclass(eq = False)
class RuleItem:
    symbol: Union[Terminal, 'NonTerminal']
    field: Optional[str]
    is_separator: bool = field(default=False)
    quantifier: Optional[Tuple[int, Optional[int]]] = field(default=None)

    def field_name(self, rule):
        if self.field is None:
            return None
        elif rule.repeating:
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
        if rule.repeating:
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
    repeating: Union[None, Literal['many'], Literal['some']]
    src_file: str
    src_line: int
    has_separator: bool = field(default=False)
    items: List[RuleItem] = field(default_factory=list)
    first_set: Optional[Set[Terminal]] = field(default=None)
    possibly_empty: Optional[bool] = field(default=None)
    generate_tostring: Union[None, Literal['exact'], Literal['approx']] = field(default=None)
    compat_extra_imports: bool = field(default=False)

    def _generate_fields(self):
        params = []
        args = []
        inits = []
        if self.repeating:
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

    def _generate_parse_core(self, indent, need_more = None, no_more = None):
        terminals = self.nonterminal.terminals
        quantified_i = 0
        separated = False
        for item in self.items:
            if isinstance(item.symbol, Terminal):
                parse = terminals.convert_token('scan$.match({}.{}, trace$)'.format(
                    terminals.terminal_type(), item.symbol.name))
                first_set = {item.symbol}
            else:
                parse = '{}.parse(scan$, trace$)'.format(item.symbol_typ(self))
                first_set = item.symbol.first_set

            if item.is_separator and not separated:
                separated = True
                if need_more:
                    yield '{}needMore$ = {};'.format(indent, need_more)
                else:
                    yield '{}needMore$ = false;'.format(indent)
                yield '{}if(!needMore$) {{'.format(indent)
                yield '{}\tswitch(scan$.getCurrentToken().terminal) {{'.format(indent)
                for first in first_set:
                    yield '{}\t\tcase {}:'.format(indent, first.name)
                yield '{}\t\t\tneedMore$ = true;'.format(indent)
                yield '{}\t\t\tbreak;'.format(indent)
                yield '{}\t\tdefault:'.format(indent)
                yield '{}\t\t\tbreak;'.format(indent)
                yield '{}\t}}'.format(indent)
                yield '{}}}'.format(indent)
                if no_more:
                    yield '{}if({})'.format(indent, no_more)
                    yield '{}\tneedMore$ = false;'.format(indent)

            if item.is_separator:
                yield '{}if(needMore$)'.format(indent)
                inner_indent = indent + '\t'
            else:
                inner_indent = indent

            if item.quantifier:
                quantified_i += 1
                if item.field:
                    yield '{}List<{t}> {} = new ArrayList<{t}>();'.format(
                        inner_indent, item.field,
                        item.symbol_typ(self)
                    )
                    if self.repeating:
                        yield '{}{f}List.add({f});'.format(inner_indent, f = item.field)
                    parse = '{}.add({})'.format(item.field, parse)
                yield from generate_quantified(
                    indent = indent,
                    terminals = terminals,
                    first_set = first_set,
                    quantified_min = item.quantifier[0],
                    quantified_max = item.quantifier[1],
                    gen = lambda indent, need_more, no_more: ['{}{};'.format(indent, parse)],
                    var_suffix = str(quantified_i)
                )
            else:
                if item.field:
                    if self.repeating:
                        parse = '{}List.add({})'.format(item.field, parse)
                    else:
                        parse = '{} {} = {}'.format(item.single_typ(self), item.field, parse)
                yield '{}{};'.format(inner_indent, parse)

    def _generate_parse(self, args):
        class_name = self.generated_class.class_name
        terminals = self.nonterminal.terminals
        yield '\tpublic static {class_name} parse(myplcc.Scan<{terminal_type}> scan$, myplcc.ITrace<{terminal_type}> trace$) {{'.format(
            class_name = class_name,
            terminal_type = terminals.terminal_type()
        )
        yield '\t\tif(trace$ != null)'
        yield '\t\t\ttrace$ = trace$.nonterm("<{}>:{}", scan$.getLineNumber());'.format(self.nonterminal.name, class_name)
        if self.repeating:
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
                quantified_min = 1 if self.repeating == 'some' else 0,
                quantified_max = None,
                explicit_rep = bool(self.has_separator),
                gen = self._generate_parse_core,
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
        if self.repeating:
            access_post = 'List.get(i)'
            indent = '\t'
            yield '\t\tfor(int i = 0; i < count; i++) {'
        else:
            access_post = ''
            indent = ''
        yield '\t\t{}str += sep;'.format(indent)
        sep = ''
        for item in self.items:
            if item.is_separator:
                yield '\t\t{}if(i < count - 1)'.format(indent)
                yield '\t\t{}\tstr += {}{};'.format(indent, sep, item.generate_tostring(self, access_post))
            else:
                yield '\t\t{}str += {}{};'.format(indent, sep, item.generate_tostring(self, access_post))
            sep = '" " + '
        if self.repeating:
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
        if self.repeating:
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
    rules = set()

    def compute_items(items, rule, *, lazy):
        first_set = set()
        possibly_empty = True
        first_sep = True
        for item in items:
            if isinstance(item.symbol, Terminal):
                next_first_set = {item.symbol}
                next_possibly_empty = False
            else:
                compute_table(item.symbol, rule)
                next_first_set = item.symbol.first_set
                next_possibly_empty = item.symbol.possibly_empty

            if item.quantifier:
                if next_possibly_empty:
                    raise RuntimeError('{}:{}: FIRST/FIRST conflict in {}:{}: quantified item cannot be possibly empty'.format(
                        rule.src_file, rule.src_line,
                        rule.nonterminal.name, rule.generated_class.class_name
                    ))
                if item.quantifier[0] == 0:
                    next_possibly_empty = True

            if item.is_separator and first_sep:
                first_sep = False
                if next_possibly_empty:
                    raise RuntimeError('{}:{}: FIRST/FIRST conflict in {}:{}: first separator cannot be possibly empty'.format(
                        rule.src_file, rule.src_line,
                        rule.nonterminal.name, rule.generated_class.class_name
                    ))

            conflict = first_set.intersection(next_first_set)
            if conflict:
                raise RuntimeError('{}:{}: FIRST/FOLLOW conflict in <{}>:{}: {}'.format(
                    rule.src_file, rule.src_line,
                    rule.nonterminal.name, rule.generated_class.name,
                    ', '.join(terminal.name for terminal in conflict)
                ))
            first_set.update(next_first_set)

            if not next_possibly_empty:
                possibly_empty = False
                if lazy:
                    return first_set, possibly_empty
                else:
                    first_set = set()
        return first_set, possibly_empty

    def compute_rule(rule):
        rules.add(rule)
        first_set, possibly_empty = compute_items(
            (item for item in rule.items if not item.is_separator),
            rule, lazy = True
        )
        if rule.repeating:
            if possibly_empty:
                raise RuntimeError('{}:{}: FIRST/FIRST conflict in <{}>:{}: repeating rule cannot be possibly empty'.format(
                    rule.src_file, rule.src_line,
                    rule.nonterminal.name, rule.generated_class.name
                ))
            if rule.has_separator:
                sep_first_set, sep_possibly_empty = compute_items(
                    rule.items, rule, lazy = True)
                first_set = first_set.union(sep_first_set)
            if rule.repeating == 'some':
                possibly_empty = True
        rule.first_set = first_set
        rule.possibly_empty = possibly_empty

    def compute_nonterm(nt):
        if isinstance(nt.rule, set):
            first_set = set()
            possibly_empty = False
            for rule in nt.rule:
                compute_table(rule, nt)
                conflict = first_set.intersection(rule.first_set)
                if conflict:
                    raise RuntimeError('FIRST/FIRST conflict in <{}>: {}'.format(
                        nt.name,
                        ', '.join(terminal.name for terminal in conflict)
                    ))
                first_set.update(rule.first_set)
                if rule.possibly_empty:
                    if possibly_empty:
                        raise RuntimeError('FIRST/FIRST conflict in <{}>: multiple possibly empty rules'.format(
                            nt.name))
                    else:
                        possibly_empty = True
            nt.first_set = first_set
            nt.possibly_empty = possibly_empty
        elif nt.rule is None:
            if isinstance(prev, GrammarRule):
                raise RuntimeError('{}:{}: use of undefined nonterminal <{}>'.format(
                    prev.src_file, prev.src_line, nt.name))
            else:
                # this should be visited again later, from a GrammarRule
                # wait until then, so we can give a better error message
                del visited[nt]
                return
        else:
            compute_table(nt.rule, nt)
            nt.first_set = nt.rule.first_set
            nt.possibly_empty = nt.rule.possibly_empty

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
                '{} {}'.format(special.__class__.__name__, special.generated_class.name)
                for special in reversed(cycle)
            ))
        visited[special] = prev

        if isinstance(special, NonTerminal):
            compute_nonterm(special)
        elif isinstance(special, GrammarRule):
            compute_rule(special)

        done.add(special)

    for cls in project.classes.values():
        compute_table(cls.special)

    for rule in rules:
        compute_items(
            (item for item in rule.items if not item.is_separator),
            rule, lazy = False
        )
        compute_items(rule.items, rule, lazy = False)
