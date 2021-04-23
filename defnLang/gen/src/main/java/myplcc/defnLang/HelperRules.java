package myplcc.defnLang;

import java.util.ArrayList;
import java.util.List;

public class HelperRules {
	public static List<myplcc.runtime.Token<Terminals>> whitespace(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		List<myplcc.runtime.Token<Terminals>> repList0$ = new ArrayList<>();
		REP0:
		while(true) {
			if(scan$.getCurrentToken().terminal != Terminals.WHITESPACE) {
				break REP0;
			}
			if(scan$.getCurrentToken().terminal == Terminals.WHITESPACE) {
				repList0$.add(scan$.take(trace$));
			} else {
				throw new RuntimeException("TODO");
			}
		}
		return repList0$;
	}

	public static Object blankLine(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		HelperRules.whitespace(scan$, trace$);
		List<Object> repList0$ = new ArrayList<>();
		REP0:
		while(repList0$.size() < 1) {
			if(scan$.getCurrentToken().terminal != Terminals.COMMENT) {
				break REP0;
			}
			if(scan$.getCurrentToken().terminal == Terminals.COMMENT) {
				scan$.take(trace$);
			} else {
				throw new RuntimeException("TODO");
			}
			List<myplcc.runtime.Token<Terminals>> repList1$ = new ArrayList<>();
			REP1:
			while(true) {
				if(scan$.getCurrentToken().terminal == Terminals.NEWLINE) {
					break REP1;
				}
				if(scan$.getCurrentToken().terminal == Terminals.NEWLINE) {
					throw new RuntimeException("TODO");
				} else {
					repList1$.add(scan$.take(trace$));
				}
			}
			repList0$.add(null);
		}
		switch(scan$.getCurrentToken().terminal) {
			case $EOF:
			case NEWLINE:
				scan$.take(trace$);
				break;
			default:
				throw new RuntimeException("TODO");
		}
		return null;
	}

	public static myplcc.runtime.Token<Terminals> nontermName(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		switch(scan$.getCurrentToken().terminal) {
			case TERMINALS:
			case TOKEN:
			case NONTERM_NAME:
				return scan$.take(trace$);
			default:
				throw new RuntimeException("TODO");
		}
	}

	public static myplcc.runtime.Token<Terminals> javaIdent(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		switch(scan$.getCurrentToken().terminal) {
			case TERMINALS:
			case TOKEN:
			case NONTERM_NAME:
			case TERMINAL_NAME:
			case IDENT:
				return scan$.take(trace$);
			default:
				throw new RuntimeException("TODO");
		}
	}

	public static myplcc.runtime.Token<Terminals> javaPathIdent(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		switch(scan$.getCurrentToken().terminal) {
			case NONTERM_NAME:
			case IDENT:
				return scan$.take(trace$);
			default:
				throw new RuntimeException("TODO");
		}
	}

	public static List<myplcc.runtime.Token<Terminals>> javaPath(myplcc.runtime.Scan<Terminals> scan$, myplcc.runtime.ITrace<Terminals> trace$) {
		List<myplcc.runtime.Token<Terminals>> repList0$ = new ArrayList<>();
		myplcc.runtime.ExplicitRepCtx repCtx0$ = new myplcc.runtime.ExplicitRepCtx();
		repCtx0$.define(true);
		while(repCtx0$.more) {
			repCtx0$.reset();
			myplcc.runtime.Token<Terminals> part;
			part = HelperRules.javaPathIdent(scan$, trace$);
			if(!repCtx0$.defined) {
				if(scan$.getCurrentToken().terminal == Terminals.DOT) {
					repCtx0$.define(true);
				}
			}
			if(repCtx0$.more) {
				if(scan$.getCurrentToken().terminal == Terminals.DOT) {
					scan$.take(trace$);
				} else {
					throw new RuntimeException("TODO");
				}
			}
			repList0$.add(part);
		}
		return repList0$;
	}
}
