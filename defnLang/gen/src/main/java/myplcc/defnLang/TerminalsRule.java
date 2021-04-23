package myplcc.defnLang;

import java.util.List;

public class TerminalsRule extends ItemRule {
	public List<myplcc.runtime.Token<Terminals>> path;

	public TerminalsRule(List<myplcc.runtime.Token<Terminals>> path) {
		this.path = path;
	}

	public static TerminalsRule parse(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		if(scan$.getCurrentToken().terminal == Terminals.TERMINALS) {
			scan$.take(trace$);
		} else {
			throw new RuntimeException("TODO");
		}
		HelperRules.whitespace(scan$, trace$);
		List<myplcc.runtime.Token<Terminals>> path;
		path = HelperRules.javaPath(scan$, trace$);
		return new TerminalsRule(path);
	}

	@Override
	public <T> T visit(ItemRule.Visitor<T> visitor) {
		return visitor.visitTerminalsRule(this);
	}
}
