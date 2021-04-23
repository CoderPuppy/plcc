package myplcc.defnLang;

public abstract class ItemRule {
	public interface Visitor<T> {
		T visitNontermRule(NontermRule o);
		T visitExtraCodeRule(ExtraCodeRule o);
		T visitTokenRule(TokenRule o);
		T visitTerminalsRule(TerminalsRule o);
	}

	public abstract <T> T visit(ItemRule.Visitor<T> visitor);

	public static ItemRule parse(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		switch(scan$.getCurrentToken().terminal) {
			case TERMINALS:
				return TerminalsRule.parse(scan$, trace$);
			case TOKEN:
			case TERMINAL_NAME:
				return TokenRule.parse(scan$, trace$);
			case NONTERM_NAME:
			case IDENT:
				return ExtraCodeRule.parse(scan$, trace$);
			case LANGLE:
				return NontermRule.parse(scan$, trace$);
			default:
				throw new RuntimeException("TODO");
		}
	}
}
