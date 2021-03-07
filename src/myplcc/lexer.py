from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional
import typing

from myplcc.project import GeneratedClass

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
class Terminals:
    generated_class: Optional[GeneratedClass] = field(init=False, default=None)
    terminals: typing.OrderedDict[str, Terminal] = field(default_factory=OrderedDict)
    compat: bool = field(default=True)

    def add(self, terminal: Terminal):
        if terminal.name in self.terminals:
            raise RuntimeError('TODO: duplicate terminal: ' + terminal.name)
        self.terminals[terminal.name] = terminal

    def terminal_type(self):
        if self.compat:
            return '{}.Val'.format(self.generated_class.class_name)
        else:
            return self.generated_class.class_name

    def token_type(self):
        if self.compat:
            return self.generated_class.class_name
        else:
            return 'myplcc.Token<{}>'.format(self.generated_class.class_name)

    def terminal_field(self):
        if self.compat:
            return 'val'
        else:
            return 'terminal'

    def generate_code(self, subs):
        if self.generated_class.package:
            yield 'package {};'.format('.'.join(self.generated_class.package))
        yield from subs('top', '')
        yield 'import myplcc.ITerminal;'
        yield from subs('import', '')
        class_name = self.generated_class.class_name
        if self.compat:
            yield 'import java.util.*;'
            yield 'import java.util.regex.*;'
            yield 'public class {} {{'.format(class_name)
            indent = '\t'
            terminal_name = 'Val'
        else:
            yield 'import java.util.regex.Pattern;'
            indent = ''
            terminal_name = class_name
        yield '{}public enum {} implements ITerminal {{'.format(indent, terminal_name)
        for terminal in self.terminals.values():
            yield '{}\t{}({}{}),'.format(indent, terminal.name, terminal.pat, ', true' if terminal.skip else '')
        yield '{}\t$EOF(null),'.format(indent)
        yield '{}\t$ERROR(null);'.format(indent)
        yield ''
        yield '{}\tpublic String pattern;'.format(indent)
        yield '{}\tpublic boolean skip;'.format(indent)
        yield '{}\tpublic Pattern cPattern;'.format(indent)
        yield ''
        yield '{}\t{}(String pattern) {{'.format(indent, terminal_name)
        yield '{}\t\tthis(pattern, false);'.format(indent)
        yield '{}\t}}'.format(indent)
        yield '{}\t{}(String pattern, boolean skip) {{'.format(indent, terminal_name)
        yield '{}\t\tthis.pattern = pattern;'.format(indent)
        yield '{}\t\tthis.skip = skip;'.format(indent)
        yield '{}\t\tif(pattern != null)'.format(indent)
        yield '{}\t\t\tthis.cPattern = Pattern.compile(pattern, Pattern.DOTALL);'.format(indent)
        yield '{}\t}}'.format(indent)
        yield ''
        yield '{}\t@Override'.format(indent)
        yield '{}\tpublic String getPattern() {{'.format(indent)
        yield '{}\t\treturn pattern;'.format(indent)
        yield '{}\t}}'.format(indent)
        yield '{}\t@Override'.format(indent)
        yield '{}\tpublic boolean isSkip() {{'.format(indent)
        yield '{}\t\treturn skip;'.format(indent)
        yield '{}\t}}'.format(indent)
        yield '{}\t@Override'.format(indent)
        yield '{}\tpublic Pattern getCompiledPattern() {{'.format(indent)
        yield '{}\t\treturn cPattern;'.format(indent)
        yield '{}\t}}'.format(indent)
        yield '{}\t@Override'.format(indent)
        yield '{}\tpublic boolean isEOF() {{'.format(indent)
        yield '{}\t\treturn this == $EOF;'.format(indent)
        yield '{}\t}}'.format(indent)
        yield '{}\t@Override'.format(indent)
        yield '{}\tpublic boolean isError() {{'.format(indent)
        yield '{}\t\treturn this == $ERROR;'.format(indent)
        yield '{}\t}}'.format(indent)
        yield from subs('Val' if self.compat else None, indent + '\t')
        yield '{}}}'.format(indent)
        if self.compat:
            yield ''
            yield '\tpublic Val val;'
            yield '\tpublic String str;'
            yield '\tpublic int lno;'
            yield ''
            yield '\tpublic {}(Val val, String str, int lno) {{'.format(class_name)
            yield '\t\tthis.val = val;'
            yield '\t\tthis.str = str;'
            yield '\t\tthis.lno = lno;'
            yield '\t}'
            yield '\tpublic {}(Val val, String str) {{'.format(class_name)
            yield '\t\tthis(val, str, 0);'
            yield '\t}'
            yield '\tpublic {}() {{'.format(class_name)
            yield '\t\tthis(null, null, 0);'
            yield '\t}'
            yield '\tpublic {}(myplcc.Token<Val> tok) {{'.format(class_name)
            yield '\t\tthis(tok.terminal, tok.str, tok.lineNum);'
            yield '\t}'
            yield ''
            yield '\tpublic String toString() {'
            yield '\t\treturn str;'
            yield '\t}'
            yield ''
            yield '\tpublic boolean isEOF() {'
            yield '\t\treturn this.val == Val.$EOF;'
            yield '\t}'
            yield from subs(None, '\t')
            yield '}'
