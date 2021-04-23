package myplcc.defnLang;

import java.util.ArrayList;
import java.util.List;

public class ExtraCodeRule extends ItemRule {
	public List<myplcc.runtime.Token<Terminals>> path;
	public List<List<myplcc.runtime.Token<Terminals>>> lines;

	public ExtraCodeRule(List<myplcc.runtime.Token<Terminals>> path, List<List<myplcc.runtime.Token<Terminals>>> lines) {
		this.path = path;
		this.lines = lines;
	}

	public static ExtraCodeRule parse(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		List<myplcc.runtime.Token<Terminals>> path;
		path = HelperRules.javaPath(scan$, trace$);
		List<Object> repList0$ = new ArrayList<>();
		REP0:
		while(true) {
		if(repList0$.size() >= 1) {
				switch(scan$.getCurrentToken().terminal) {
					case COMMENT:
					case $EOF:
					case WHITESPACE:
					case NEWLINE:
						break;
					default:
						break REP0;
				}
			}
			repList0$.add(HelperRules.blankLine(scan$, trace$));
		}
		HelperRules.whitespace(scan$, trace$);
		if(scan$.getCurrentToken().terminal == Terminals.EXTRA_CODE_SEP) {
			scan$.take(trace$);
		} else {
			throw new RuntimeException("TODO");
		}
		HelperRules.blankLine(scan$, trace$);
		List<List<myplcc.runtime.Token<Terminals>>> lines;
		List<List<myplcc.runtime.Token<Terminals>>> repList1$ = new ArrayList<>();
		REP1:
		while(true) {
			if(scan$.getCurrentToken().terminal == Terminals.EXTRA_CODE_SEP) {
				break REP1;
			}
			List<List<myplcc.runtime.Token<Terminals>>> tokens_;
			List<List<myplcc.runtime.Token<Terminals>>> repList2$ = new ArrayList<>();
			REP2:
			while(repList2$.size() < 1) {
				switch(scan$.getCurrentToken().terminal) {
					case EXTRA_CODE_SEP:
					case NEWLINE:
						break REP2;
					default:
				}
				myplcc.runtime.Token<Terminals> initial;
				switch(scan$.getCurrentToken().terminal) {
					case EXTRA_CODE_SEP:
					case NEWLINE:
						throw new RuntimeException("TODO");
					default:
						initial = scan$.take(trace$);
				}
				List<myplcc.runtime.Token<Terminals>> tokens__;
				List<myplcc.runtime.Token<Terminals>> repList3$ = new ArrayList<>();
				REP3:
				while(true) {
					if(scan$.getCurrentToken().terminal == Terminals.NEWLINE) {
						break REP3;
					}
					if(scan$.getCurrentToken().terminal == Terminals.NEWLINE) {
						throw new RuntimeException("TODO");
					} else {
						repList3$.add(scan$.take(trace$));
					}
				}
				tokens__ = repList3$;
				tokens__.add(0, initial);
				repList2$.add(tokens__);
			}
			tokens_ = repList2$;
			myplcc.runtime.Token<Terminals> newline;
			if(scan$.getCurrentToken().terminal == Terminals.NEWLINE) {
				newline = scan$.take(trace$);
			} else {
				throw new RuntimeException("TODO");
			}
			List<myplcc.runtime.Token<Terminals>> whitespace;
			whitespace = HelperRules.whitespace(scan$, trace$);
			List<myplcc.runtime.Token<Terminals>> tokens = tokens_.isEmpty() ? new ArrayList<>() : tokens_.get(0);
			tokens.add(newline);
			tokens.addAll(whitespace);
			repList1$.add(tokens);
		}
		lines = repList1$;
		if(scan$.getCurrentToken().terminal == Terminals.EXTRA_CODE_SEP) {
			scan$.take(trace$);
		} else {
			throw new RuntimeException("TODO");
		}
		HelperRules.blankLine(scan$, trace$);
		return new ExtraCodeRule(path, lines);
	}

	@Override
	public <T> T visit(ItemRule.Visitor<T> visitor) {
		return visitor.visitExtraCodeRule(this);
	}
}
