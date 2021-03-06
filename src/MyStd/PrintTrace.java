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

	public void print(String s, int lno) {
		if (out != null)
			out.printf("%4d: %s\n", lno, indent + s);
	}
	public void print(Token<T> t) {
		print(t.terminal.toString()+" \""+t.toString()+"\"", t.lno);
	}
	public ITrace<T> nonterm(String s, int lno) {
		print(s, lno);
		return new PrintTrace<T>(out, indent + "| ");
	}
	public void reset() {
		indent = "";
	}
}
