package myplcc.runtime;

public interface ITrace<T extends ITerminal> {
	void print(Token<T> t);

	void print(String s, int lineNum);

	ITrace<T> nonterm(String s, int lineNum);

	void reset();
}
