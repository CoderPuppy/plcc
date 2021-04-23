package myplcc.lexer;

public class Terminal {
	public final Terminals terminals;
	public final String name;
	public final String pattern;
	public final boolean skip;

	public Terminal(Terminals terminals, String name, String pattern, boolean skip) {
		this.terminals = terminals;
		this.name = name;
		this.pattern = pattern;
		this.skip = skip;
		assert !terminals.terminals.containsKey(name);
		terminals.terminals.put(name, this);
	}
}
