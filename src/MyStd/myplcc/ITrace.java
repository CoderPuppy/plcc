package myplcc;

public interface ITrace<T extends ITerminal> {
	public void print(Token<T> t);
	public void print(String s, int lineNum);
	public ITrace<T> nonterm(String s, int lineNum);
	public void reset();
}
