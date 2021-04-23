package myplcc.grammar;

import myplcc.ClassRef;
import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.Utils;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.util.Set;
import java.util.function.Consumer;

public class Repeated implements Element {
	public final Element element;
	public final int min;
	public final Integer max;

	public Repeated(Element element, int min, Integer max) {
		this.element = element;
		assert min >= 0;
		this.min = min;
		assert max == null || max >= min;
		this.max = max;
	}

	@Override
	public Set<Terminal> getFirstSet() {
		return element.getFirstSet();
	}

	@Override
	public boolean isPossiblyEmpty() {
		return min == 0;
	}

	@Override
	public void checkLL1() {
		assert !element.isPossiblyEmpty();
		element.checkLL1();
	}

	@Override
	public TypeRef getOutputType() {
		return new TypeRef.List(element.getOutputType());
	}

	@Override
	public Terminals getTerminals() {
		return element.getTerminals();
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		Element.super.addImports(doImport);
		element.addImports(doImport);
		doImport.accept(ClassRef.util("ArrayList"));
	}

	@Override
	public Generator.Method generateParse(Generator.ExprSink after, String _explicitRepCtx) {
		return (ctx, indent) -> {
			String suffix = Integer.toString(ctx.suffix);
			ctx.suffix += 1;
			ctx.output.append(indent);
			getOutputType().generate(ctx.output);
			ctx.output.append(" repList");
			ctx.output.append(suffix);
			ctx.output.append("$ = new ArrayList<>();\n");

			if(element.hasSeparator()) {
				ctx.output.append(indent);
				ctx.output.append("myplcc.runtime.ExplicitRepCtx repCtx");
				ctx.output.append(suffix);
				ctx.output.append('$');
				ctx.output.append(" = new myplcc.runtime.ExplicitRepCtx();\n");

				// determine whether to start the loop
				if(min > 0) {
					// always true to get to the min
					ctx.output.append(indent);
					ctx.output.append("repCtx");
					ctx.output.append(suffix);
					ctx.output.append("$.define(true);\n");
				} else {
					// determine from the first set
					Utils.generateBinarySwitch(element.getFirstSet(),
						(ctx1, indent1) -> {
							ctx1.output.append(indent1);
							ctx1.output.append("repCtx");
							ctx1.output.append(suffix);
							ctx1.output.append("$.define(true);\n");
							return true;
						},
						(ctx1, indent1) -> {
							ctx1.output.append(indent1);
							ctx1.output.append("repCtx");
							ctx1.output.append(suffix);
							ctx1.output.append("$.define(false);\n");
							return true;
						}
					).generate(ctx, indent);
				}

				ctx.output.append(indent);
				ctx.output.append("while(repCtx");
				ctx.output.append(suffix);
				ctx.output.append("$.more) {\n");
				ctx.output.append(indent);
				ctx.output.append("\trepCtx");
				ctx.output.append(suffix);
				ctx.output.append("$.reset();\n");
				if(min > 1) {
					// require more until the min is met
					ctx.output.append(indent);
					ctx.output.append("\tif(repList");
					ctx.output.append(suffix);
					ctx.output.append("$.size() < ");
					ctx.output.append(Integer.toString(min - 1));
					ctx.output.append(")\n");
					ctx.output.append(indent);
					ctx.output.append("\t\trepCtx");
					ctx.output.append(suffix);
					ctx.output.append("$.define(true);\n");
				}
				if(max != null) {
					// deny more after the max is filled
					ctx.output.append(indent);
					ctx.output.append("if(repList");
					ctx.output.append(suffix);
					ctx.output.append("$.size() >= ");
					ctx.output.append(Integer.toString(max - 1));
					ctx.output.append(")\n");
					ctx.output.append(indent);
					ctx.output.append("\trepCtx");
					ctx.output.append(suffix);
					ctx.output.append("$.define(false);\n");
				}
			} else { // no separator, just min/max and first set
				ctx.output.append(indent);
				ctx.output.append("REP");
				ctx.output.append(suffix);
				ctx.output.append(":\n");
				ctx.output.append(indent);
				if(max == null) {
					ctx.output.append("while(true) {\n");
				} else {
					ctx.output.append("while(repList");
					ctx.output.append(suffix);
					ctx.output.append("$.size() < ");
					ctx.output.append(Integer.toString(max));
					ctx.output.append(") {\n");
				}

				String indent_ = indent + "\t";
				if(min > 0) {
					indent_ += "\t";
					ctx.output.append(indent);
					ctx.output.append("if(repList");
					ctx.output.append(suffix);
					ctx.output.append("$.size() >= ");
					ctx.output.append(Integer.toString(min));
					ctx.output.append(") {\n");
				}
				Utils.generateBinarySwitch(element.getFirstSet(),
					null,
					(ctx1, indent1) -> {
						ctx1.output.append(indent1);
						ctx1.output.append("break REP");
						ctx1.output.append(suffix);
						ctx1.output.append(";\n");
						return false;
					}
				).generate(ctx, indent_);
				if(min > 0) {
					ctx.output.append(indent);
					ctx.output.append("\t}\n");
				}
			}

			element.generateParse((expr, required) -> (ctx1, indent1) -> {
				ctx1.output.append(indent1);
				ctx1.output.append("repList");
				ctx1.output.append(suffix);
				ctx1.output.append("$.add(");
				ctx1.output.append(expr);
				ctx1.output.append(");\n");
				return true;
			}, element.hasSeparator() ? "repCtx" + suffix + "$" : null).generate(ctx, indent + "\t");

			ctx.output.append(indent);
			ctx.output.append("}\n");

			return after.withExpr("repList" + suffix + "$", false).generate(ctx, indent);
		};
	}
}
