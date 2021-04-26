package myplcc.grammar;

import myplcc.ClassRef;
import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.Utils;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.util.Set;
import java.util.function.Consumer;

public class Context implements Element {
	public final String label;
	public final Element element;

	public Context(String label, Element element) {
		this.label = label;
		this.element = element;
	}

	@Override
	public Set<Terminal> getFirstSet() {
		return element.getFirstSet();
	}

	@Override
	public boolean isPossiblyEmpty() {
		return element.isPossiblyEmpty();
	}

	@Override
	public TypeRef getOutputType() {
		return element.getOutputType();
	}

	@Override
	public void checkLL1() {
		assert !element.isPossiblyEmpty();
	}

	@Override
	public boolean hasSeparator() {
		return element.hasSeparator();
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		Element.super.addImports(doImport);
		element.addImports(doImport);
	}

	@Override
	public Terminals getTerminals() {
		return element.getTerminals();
	}

	@Override
	public Generator.Method generateParse(Generator.ExprSink after, String explicitRepCtx) {
		return (ctx, indent) -> {
			ctx.output.append(indent);
			ctx.output.append("parse$.enter(");
			ctx.output.append(Utils.escapeString(label));
			ctx.output.append(");\n");
			return element.generateParse((expr, required) -> (ctx1, indent1) -> {
				ctx1.output.append(indent1);
				ctx1.output.append("parse$.leave();\n");
				return after.withExpr(expr, required).generate(ctx1, indent1);
			}, explicitRepCtx).generate(ctx, indent);
		};
	}
}
