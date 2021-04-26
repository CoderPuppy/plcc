package myplcc.runtime;

public interface IParseState<T extends ITerminal> {
	T getCurrentTerminal();

	Token<T> take();

	void enter(String ctx);

	void leave();
}
