package myplcc;

public class Token<T extends ITerminal> {
	public T terminal;
	public String str;
	public int lno;

	public Token(T terminal, String str, int lno) {
		this.terminal = terminal;
		this.str = str;
		this.lno = lno;
	}
}
