package myplcc.grammar;

import myplcc.ClassRef;
import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.io.IOException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Collectors;

public class Alternative implements Element {
	private final TypeRef typeRef;
	public final Set<Element> alternatives;
	private Set<Terminal> firstSet = null;
	private Element possiblyEmpty = null;
	private boolean hasSeparator = false;

	public Alternative(TypeRef typeRef, Element... alternatives) {
		this(typeRef, Arrays.stream(alternatives).collect(Collectors.toSet()));
	}
	public Alternative(TypeRef typeRef, Set<Element> alternatives) {
		this.typeRef = typeRef;
		this.alternatives = alternatives;
	}

	private void compute() {
		if(firstSet != null)
			return;
		firstSet = new HashSet<>();
		for(Element alt : alternatives) {
			if(alt.hasSeparator()) hasSeparator = true;

			Set<Terminal> intersection = new HashSet<>(firstSet);
			intersection.retainAll(alt.getFirstSet());
			if(!intersection.isEmpty()) {
				throw new RuntimeException("TODO: conflict: " +
					intersection.stream().map(terminal -> terminal.name).collect(Collectors.joining(", ")));
			}

			firstSet.addAll(alt.getFirstSet());

			if(alt.isPossiblyEmpty()) {
				if(possiblyEmpty == null)
					possiblyEmpty = alt;
				else
					throw new RuntimeException("TODO: conflict (possibly empty)");
			}
		}
	}

	@Override
	public Set<Terminal> getFirstSet() {
		compute();
		return firstSet;
	}

	@Override
	public boolean isPossiblyEmpty() {
		compute();
		return possiblyEmpty != null;
	}

	@Override
	public void checkLL1() {
		compute();
		for(Element alt : alternatives) {
			assert alt.hasSeparator() == hasSeparator;
			alt.checkLL1();
		}
	}

	@Override
	public boolean hasSeparator() {
		return hasSeparator;
	}

	@Override
	public TypeRef getOutputType() {
		return typeRef;
	}

	@Override
	public Terminals getTerminals() {
		return alternatives.iterator().next().getTerminals();
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		Element.super.addImports(doImport);
		for(Element alternative : alternatives) {
			alternative.addImports(doImport);
		}
	}

	@Override
	public Generator.Method generateParse(Generator.ExprSink after, String explicitRepCtx) {
		return (ctx, indent) -> {
			boolean returns = false;
			ctx.output.append(indent);
			ctx.output.append("switch(parse$.getCurrentTerminal()) {\n");

			for(Element alt : alternatives) {
				if(alt == possiblyEmpty) continue;
				for(Terminal t : alt.getFirstSet()) {
					ctx.output.append(indent);
					ctx.output.append("\tcase ");
					ctx.output.append(t.name);
					ctx.output.append(":\n");
				}
				if(alt.generateParse(after, explicitRepCtx).generate(ctx, indent + "\t\t")) {
					returns = true;
					ctx.output.append(indent);
					ctx.output.append("\t\tbreak;\n");
				}
			}

			ctx.output.append(indent);
			ctx.output.append("\tdefault:\n");
			if(possiblyEmpty == null) {
				ctx.output.append(indent);
				ctx.output.append("\t\tthrow new myplcc.runtime.ParseException(\"expected ");
				boolean firstAlt = true;
				for(Element alt : alternatives) {
					if(!firstAlt)
						ctx.output.append("; or ");
					firstAlt = false;

					Terminal last = null;
					boolean first = true;
					for(Terminal t : alt.getFirstSet()) {
						if(last != null) {
							if(!first)
								ctx.output.append(", ");
							first = false;
							ctx.output.append(last.name);
						}
						last = t;
					}
					assert last != null;
					if(!first)
						ctx.output.append(" or ");
					ctx.output.append(last.name);

					ctx.output.append(" for ");
					ctx.output.append(alt.toString());
				}
				ctx.output.append("\");\n");
			} else {
				if(possiblyEmpty.generateParse(after, explicitRepCtx).generate(ctx, indent + "\t\t")) {
					returns = true;
					ctx.output.append(indent);
					ctx.output.append("\t\tbreak;\n");
				}
			}

			ctx.output.append(indent);
			ctx.output.append("}\n");
			return returns;
		};
	}
}