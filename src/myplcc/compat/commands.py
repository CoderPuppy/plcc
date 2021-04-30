from dataclasses import dataclass, field
from typing import Optional

from myplcc.project import GeneratedClass
from myplcc.lexer import Terminals
from myplcc.grammar import NonTerminal

@dataclass(eq = False)
class Scan:
    terminals: Terminals
    generated_class: Optional[GeneratedClass] = field(default=None)

    def generate_code(self, subs):
        if self.generated_class.package:
            yield 'package {};'.format('.'.join(self.generated_class.package))
        yield 'import java.io.BufferedReader;'
        yield 'import java.io.InputStreamReader;'
        yield 'import java.io.StringReader;'
        yield from self.terminals.generated_class.import_(self.generated_class.package)
        # TODO: extra code?
        # TODO: implements IScan
        yield 'public class {} {{'.format(self.generated_class.class_name)
        yield '\tprivate BufferedReader rdr;'.format(self.terminals.terminal_type())
        yield '\tprivate myplcc.Scan<{}> scan;'.format(self.terminals.terminal_type())
        yield '\tpublic int lno;'
        yield '\tpublic {} tok;'.format(self.terminals.token_type())
        yield ''
        yield '\tpublic {}(BufferedReader rdr) {{'.format(self.generated_class.class_name)
        yield '\t\tthis.rdr = rdr;'
        yield '\t\tscan = new myplcc.Scan<{t}>({t}.set, rdr, lno);'.format(t = self.terminals.terminal_type())
        yield '\t\treset();'
        yield '\t}'
        yield '\tpublic {}(String s) {{'.format(self.generated_class.class_name)
        yield '\t\tthis(new BufferedReader(new StringReader(s)));'
        yield '\t}'
        yield ''
        yield '\tpublic void reset() {'
        yield '\t\ttok = null;'
        yield '\t\tscan.empty();'
        yield '\t}'
        yield '\tpublic void fillString() {'
        # TODO: this is hacky
        yield '\t\tscan.getCurrentToken();'
        yield '\t\tlno = scan.getLineNumber();'
        yield '\t}'
        yield '\tpublic {} cur() {{'.format(self.terminals.token_type())
        yield '\t\ttok = {};'.format(self.terminals.convert_token('scan.getCurrentToken()'))
        yield '\t\tlno = scan.getLineNumber();'
        yield '\t\treturn tok;'
        yield '\t}'
        yield '\tpublic void adv() {'
        yield '\t\tscan.next();'
        yield '\t\ttok = null;'
        yield '\t\tlno = scan.getLineNumber();'
        yield '\t}'
        yield '\tpublic void put({} t) {{'.format(self.terminals.token_type())
        yield '\t\tthrow new RuntimeException("Scan class: put not implemented");'
        yield '\t}'
        # TODO: this is not strictly compatible, due to the trace nonsense
        yield '\tpublic {tok} match({term} v, myplcc.ITrace<{term}> trace) {{'.format(
            tok = self.terminals.token_type(),
            term = self.terminals.terminal_type()
        )
        yield '\t\treturn {};'.format(self.terminals.convert_token('scan.match(v, trace)'))
        yield '\t}'
        yield '\tpublic boolean isEOF() {'
        yield '\t\treturn cur().isEOF();'
        yield '\t}'
        yield '\tpublic void printTokens() {'
        yield '\t\twhile(hasNext()) {'
        yield '\t\t\t{} t = next();'.format(self.terminals.token_type())
        yield '\t\t\tString s;'
        yield '\t\t\tif(t.{} == {}.$ERROR)'.format(self.terminals.terminal_field(), self.terminals.terminal_type())
        yield '\t\t\t\ts = String.format("ERROR \'%s\'", t.str);'
        yield '\t\t\telse'
        yield '\t\t\t\ts = String.format("%s \'%s\'", t.{}, t.str);'.format(self.terminals.terminal_field())
        yield '\t\t\tSystem.out.println(String.format("%4d: %s", lno, s));'
        yield '\t\t}'
        yield '\t}'
        yield '\tpublic boolean hasNext() {'
        yield '\t\treturn !cur().isEOF();'
        yield '\t}'
        yield '\tpublic {} next() {{'.format(self.terminals.token_type())
        yield '\t\t{} t = cur();'.format(self.terminals.token_type())
        yield '\t\tadv();'
        yield '\t\treturn t;'
        yield '\t}'
        yield '\tpublic static void main(String[] args) {'
        yield '\t\tBufferedReader rdr = new BufferedReader(new InputStreamReader(System.in));'
        yield '\t\t{n} scn = new {n}(rdr);'.format(n = self.generated_class.class_name)
        yield '\t\tscn.printTokens();'
        yield '\t}'
        yield '}'

@dataclass(eq = False)
class Parser:
    nonterminal: NonTerminal
    generated_class: Optional[GeneratedClass] = field(default=None)

    def generate_code(self, subs):
        terminals = self.nonterminal.terminals
        if self.generated_class.package:
            yield 'package {};'.format('.'.join(self.generated_class.package))
        yield 'import java.io.Reader;'
        yield 'import java.io.BufferedReader;'
        yield 'import java.io.InputStreamReader;'
        yield 'import java.io.StringReader;'
        yield from terminals.generated_class.import_(self.generated_class.package)
        yield from self.nonterminal.generated_class.import_(self.generated_class.package)
        # TODO: extra code?
        yield 'public class {} {{'.format(self.generated_class.class_name)
        yield '\tprivate static void parse(Reader r, myplcc.ITrace<{}> trace) {{'.format(terminals.terminal_type())
        yield '\t\ttry {'
        yield '\t\t\tBufferedReader rdr = new BufferedReader(r);'
        yield '\t\t\tmyplcc.Scan<{t}> scn = new myplcc.Scan<{t}>({t}.set, rdr, 0);'.format(
            t = terminals.terminal_type())
        yield '\t\t\tSystem.out.println({}.parse(scn, trace));'.format(self.nonterminal.generated_class.class_name)
        yield '\t\t} catch(NullPointerException e) {'
        yield '\t\t\tSystem.out.println("Premature end of input");'
        yield '\t\t} catch(Exception e) {'
        yield '\t\t\tSystem.out.println(e);'
        yield '\t\t}'
        yield '\t}'
        yield '\tpublic static void main(String[] args) {'
        yield '\t\tmyplcc.ITrace<{}> trace = null;'.format(terminals.terminal_type())
        yield '\t\tint firstArg = 0;'
        yield '\t\tif(args.length > 0 && args[0].equals("-t")) {'
        yield '\t\t\ttrace = new myplcc.PrintTrace<{}>();'.format(terminals.terminal_type())
        yield '\t\t\tSystem.out.println("tracing ...");'
        yield '\t\t\tfirstArg++;'
        yield '\t\t}'
        yield '\t\tif(firstArg == args.length) {'
        yield '\t\t\tparse(new InputStreamReader(System.in), trace);'
        yield '\t\t\treturn;'
        yield '\t\t}'
        yield '\t\tfor(int i = firstArg; i < args.length; i++) {'
        yield '\t\t\tString arg = args[i];'
        yield '\t\t\tif(trace != null) {'
        yield '\t\t\t\ttrace.reset();'
        yield '\t\t\t\tSystem.out.println();'
        yield '\t\t\t}'
        yield '\t\t\tSystem.out.println(arg + " -> ");'
        yield '\t\t\tparse(new StringReader(arg), trace);'
        yield '\t\t}'
        yield '\t}'
        yield '}'

@dataclass(eq = False)
class Rep:
    nonterminal: NonTerminal
    generated_class: Optional[GeneratedClass] = field(default=None)

    def generate_code(self, subs):
        terminals = self.nonterminal.terminals
        if self.generated_class.package:
            yield 'package {};'.format('.'.join(self.generated_class.package))
        yield from terminals.generated_class.import_(self.generated_class.package)
        yield from self.nonterminal.generated_class.import_(self.generated_class.package)
        yield 'import java.io.BufferedReader;'
        yield 'import java.io.InputStreamReader;'
        yield 'import java.io.FileReader;'
        yield 'import java.io.FileNotFoundException;'
        # TODO: extra code?
        yield 'public class {} {{'.format(self.generated_class.class_name)
        yield '\tpublic static void main(String[] args) {'
        yield '\t\tmyplcc.ITrace<{}> trace = null;'.format(terminals.terminal_type())
        yield '\t\tString prompt = "--> ";'
        yield '\t\tfor(String arg : args) {'
        yield '\t\t\tif(arg.equals("-n"))'
        yield '\t\t\t\tprompt = "";'
        yield '\t\t\telse if(arg.equals("-t"))'
        yield '\t\t\t\ttrace = new myplcc.PrintTrace<{}>();'.format(terminals.terminal_type())
        yield '\t\t\telse {'
        yield '\t\t\t\tBufferedReader reader = null;'
        yield '\t\t\t\ttry {'
        yield '\t\t\t\t\treader = new BufferedReader(new FileReader(arg));'
        yield '\t\t\t\t} catch(FileNotFoundException e) {'
        yield '\t\t\t\t\tSystem.out.println(arg + ": no such file ... exiting");'
        yield '\t\t\t\t\tSystem.exit(1);'
        yield '\t\t\t\t}'
        yield '\t\t\t\tmyplcc.Scan<{t}> scan = new myplcc.Scan<{t}>({t}.set, reader, 0);'.format(
            t = terminals.terminal_type())
        yield '\t\t\t\ttry {'
        yield '\t\t\t\t\twhile(true) {'
        yield '\t\t\t\t\t\tif(trace != null)'
        yield '\t\t\t\t\t\t\ttrace.reset();'
        yield '\t\t\t\t\t\tif(scan.getCurrentToken().isEOF())'
        yield '\t\t\t\t\t\t\tbreak;'
        yield '\t\t\t\t\t\tSystem.out.println({}.parse(scan, trace));'.format(self.nonterminal.generated_class.class_name)
        yield '\t\t\t\t\t}'
        yield '\t\t\t\t} catch(Exception e) {'
        yield '\t\t\t\t\tSystem.out.println(e.getMessage());'
        yield '\t\t\t\t} catch(Error e) {'
        yield '\t\t\t\t\tSystem.out.println(e.getMessage());'
        yield '\t\t\t\t\tSystem.exit(1);'
        yield '\t\t\t\t}'
        yield '\t\t\t}'
        yield '\t\t}'
        yield '\t\tBufferedReader reader = new BufferedReader(new InputStreamReader(System.in));'
        yield '\t\tmyplcc.Scan<{t}> scan = new myplcc.Scan<{t}>({t}.set, reader, 0);'.format(
            t = terminals.terminal_type())
        yield '\t\twhile(true) {'
        yield '\t\t\tSystem.out.print(prompt);'
        yield '\t\t\ttry {'
        yield '\t\t\t\tif(scan.getCurrentToken().isEOF()) {'
        yield '\t\t\t\t\tSystem.out.println();'
        yield '\t\t\t\t\tbreak;'
        yield '\t\t\t\t}'
        yield '\t\t\t\tif(trace != null) {'
        yield '\t\t\t\t\ttrace.reset();'
        yield '\t\t\t\t\tSystem.out.println();'
        yield '\t\t\t\t}'
        yield '\t\t\t\tSystem.out.println({}.parse(scan, trace));'.format(self.nonterminal.generated_class.class_name)
        yield '\t\t\t} catch(Exception e) {'
        yield '\t\t\t\tSystem.out.println(e.getMessage());'
        yield '\t\t\t\tscan = new myplcc.Scan<{t}>({t}.set, reader, scan.getLineNumber());'.format(
            t = terminals.terminal_type())
        yield '\t\t\t} catch(Error e) {'
        yield '\t\t\t\tSystem.out.println(e.getMessage());'
        yield '\t\t\t\tSystem.exit(1);'
        yield '\t\t\t}'
        yield '\t\t}'
        yield '\t}'
        yield '}'
