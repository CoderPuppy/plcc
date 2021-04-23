package myplcc.defnLang;

import java.util.ArrayList;
import java.util.List;

public class TokenRule extends ItemRule {
	public Terminals tokenType;
	public myplcc.runtime.Token<Terminals> name;
	public myplcc.runtime.Token<Terminals> pattern;

	public TokenRule(Terminals tokenType, myplcc.runtime.Token<Terminals> name, myplcc.runtime.Token<Terminals> pattern) {
		this.tokenType = tokenType;
		this.name = name;
		this.pattern = pattern;
	}

	public static TokenRule parse(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		Terminals tokenType;
		List<myplcc.runtime.Token<Terminals>> tokenTypeList;
		List<myplcc.runtime.Token<Terminals>> repList0$ = new ArrayList<>();
		REP0:
		while(repList0$.size() < 1) {
			if(scan$.getCurrentToken().terminal != Terminals.TOKEN) {
				break REP0;
			}
			myplcc.runtime.Token<Terminals> token;
			if(scan$.getCurrentToken().terminal == Terminals.TOKEN) {
				token = scan$.take(trace$);
			} else {
				throw new RuntimeException("TODO");
			}
			HelperRules.whitespace(scan$, trace$);
			repList0$.add(token);
		}
		tokenTypeList = repList0$;
		tokenType = tokenTypeList.isEmpty() ? Terminals.TOKEN : tokenTypeList.get(0).terminal;
		myplcc.runtime.Token<Terminals> name;
		if(scan$.getCurrentToken().terminal == Terminals.TERMINAL_NAME) {
			name = scan$.take(trace$);
		} else {
			throw new RuntimeException("TODO");
		}
		HelperRules.whitespace(scan$, trace$);
		myplcc.runtime.Token<Terminals> pattern;
		switch(scan$.getCurrentToken().terminal) {
			case STR:
			case RAW_STR:
				pattern = scan$.take(trace$);
				break;
			default:
				throw new RuntimeException("TODO");
		}
		return new TokenRule(tokenType, name, pattern);
	}

	@Override
	public <T> T visit(ItemRule.Visitor<T> visitor) {
		return visitor.visitTokenRule(this);
	}
}
