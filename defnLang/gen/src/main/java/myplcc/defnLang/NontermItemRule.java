package myplcc.defnLang;

import java.util.List;

public class NontermItemRule {
	public NontermItemRule() {
	}

	public static NontermItemRule parse(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		HelperRules.whitespace(scan$, trace$);
		return new NontermItemRule();
	}
}
