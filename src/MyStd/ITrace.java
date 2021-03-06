public interface ITrace<T extends ITerminal> {
	public void print(Token<T> t);
	public void print(String s, int lno);
	public ITrace<T> nonterm(String s, int lno);
	public void reset();
}
