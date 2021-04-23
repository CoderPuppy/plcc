package myplcc.defnLang;

import java.util.ArrayList;
import java.util.List;

public class NontermRule extends ItemRule {
	public myplcc.runtime.Token<Terminals> name;
	public myplcc.runtime.Token<Terminals> type;
	public List<NontermItemRule> items;

	public NontermRule(myplcc.runtime.Token<Terminals> name, myplcc.runtime.Token<Terminals> type, List<NontermItemRule> items) {
		this.name = name;
		this.type = type;
		this.items = items;
	}

	public static NontermRule parse(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		if(scan$.getCurrentToken().terminal == Terminals.LANGLE) {
			scan$.take(trace$);
		} else {
			throw new RuntimeException("TODO");
		}
		HelperRules.whitespace(scan$, trace$);
		myplcc.runtime.Token<Terminals> name;
		name = HelperRules.nontermName(scan$, trace$);
		HelperRules.whitespace(scan$, trace$);
		if(scan$.getCurrentToken().terminal == Terminals.RANGLE) {
			scan$.take(trace$);
		} else {
			throw new RuntimeException("TODO");
		}
		HelperRules.whitespace(scan$, trace$);
		myplcc.runtime.Token<Terminals> type;
		switch(scan$.getCurrentToken().terminal) {
			case RULE_DEF:
			case REPEATING_RULE_DEF:
				type = scan$.take(trace$);
				break;
			default:
				throw new RuntimeException("TODO");
		}
		List<NontermItemRule> items;
		List<NontermItemRule> repList0$ = new ArrayList<>();
		REP0:
		while(true) {
			if(scan$.getCurrentToken().terminal != Terminals.WHITESPACE) {
				break REP0;
			}
			repList0$.add(NontermItemRule.parse(scan$, trace$));
		}
		items = repList0$;
		return new NontermRule(name, type, items);
	}

	@Override
	public <T> T visit(ItemRule.Visitor<T> visitor) {
		return visitor.visitNontermRule(this);
	}
}
