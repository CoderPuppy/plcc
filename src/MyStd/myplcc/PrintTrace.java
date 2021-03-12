package myplcc;

import java.io.PrintStream;

public class PrintTrace<T extends ITerminal> implements ITrace<T> {
	public String indent;
	public PrintStream out;

	public PrintTrace(PrintStream out, String indent) {
		this.out = out;
		this.indent = indent;
	}
	public PrintTrace(PrintStream out) {
		this(out, "");
	}
	public PrintTrace() {
		this(System.err); // output defaults to System.err
	}

	public void print(String s, int lineNum) {
		if (out != null)
			out.printf("%4d: %s\n", lineNum, indent + s);
	}
	public void print(Token<T> t) {
		print(t.terminal + " \"" + t.str + "\"", t.lineNum);
	}
	public ITrace<T> nonterm(String s, int lineNum) {
		print(s, lineNum);
		return new PrintTrace<T>(out, indent + "| ");
	}
	public void reset() {
		indent = "";
	}
}
