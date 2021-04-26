package myplcc.grammar;

import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.Utils;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;
import myplcc.lexer.Token;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

public class TerminalClass implements Element {
	public final Token token;
	public final Set<Terminal> terminals;

	public TerminalClass(Token token, Terminal... terminals) {
		this(token, Arrays.stream(terminals).collect(Collectors.toSet()));
	}

	public TerminalClass(Token token, Set<Terminal> terminals) {
		this.token = token;
		this.terminals = terminals;
		assert terminals.stream().allMatch(t -> t.terminals == token.getTerminals());
	}

	@Override
	public Set<Terminal> getFirstSet() {
		return terminals;
	}

	@Override
	public boolean isPossiblyEmpty() {
		return false;
	}

	@Override
	public TypeRef getOutputType() {
		return token;
	}

	@Override
	public Terminals getTerminals() {
		return token.getTerminals();
	}

	@Override
	public Generator.Method generateParse(Generator.ExprSink after, String explicitRepCtx) {
		return (ctx, indent) -> {
			// special case: all terminals, so don't bother generating cases
			if(terminals.equals(new HashSet<>(token.getTerminals().terminals.values())))
				return after.withExpr("parse$.take()", true).generate(ctx, indent);

			return Utils.generateBinarySwitch(terminals,
				(ctx1, indent1) -> after.withExpr("parse$.take()", true).generate(ctx1, indent1),
				(ctx1, indent1) -> {
					ctx1.output.append(indent1);
					ctx1.output.append("throw new myplcc.runtime.ParseException(\"expected ");
					Terminal last = null;
					boolean first = true;
					for(Terminal terminal : terminals) {
						if(last != null) {
							if(!first)
								ctx1.output.append(", ");
							first = false;
							ctx1.output.append(last.name);
						}
						last = terminal;
					}
					assert last != null;
					if(!first)
						ctx1.output.append(" or ");
					ctx1.output.append(last.name);
					ctx1.output.append("\");\n");
					return false;
				}
			).generate(ctx, indent);
		};
	}
}
