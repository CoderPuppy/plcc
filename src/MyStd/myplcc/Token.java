package myplcc;

public class Token<T extends ITerminal> {
	public T terminal;
	public String str;
	public int lineNum;

	public Token(T terminal, String str, int lineNum) {
		this.terminal = terminal;
		this.str = str;
		this.lineNum = lineNum;
	}

	public boolean isEOF() {
		return terminal.isEOF();
	}
}
