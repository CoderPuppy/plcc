package myplcc.grammar;

import myplcc.ClassRef;
import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.Utils;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.io.IOException;
import java.util.Set;
import java.util.function.Consumer;

public class Separator implements Element {
	public final Element element;

	public Separator(Element element) {
		this.element = element;
	}

	@Override
	public Set<Terminal> getFirstSet() {
		return element.getFirstSet();
	}

	@Override
	public boolean isPossiblyEmpty() {
		return true;
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
		return true;
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
			// TODO: skip if must already be defined
			ctx.output.append(indent);
			ctx.output.append("if(!");
			ctx.output.append(explicitRepCtx);
			ctx.output.append(".defined) {\n");
			Utils.generateBinarySwitch(element.getFirstSet(),
				(ctx1, indent1) -> {
					ctx1.output.append(indent1);
					ctx1.output.append(explicitRepCtx);
					ctx1.output.append(".define(true);\n");
					return true;
				},
				null
			).generate(ctx, indent + "\t");
			ctx.output.append(indent);
			ctx.output.append("}\n");
			ctx.output.append(indent);
			ctx.output.append("if(");
			ctx.output.append(explicitRepCtx);
			ctx.output.append(".more) {\n");
			boolean returns = element.generateParse(after, explicitRepCtx).generate(ctx, indent + "\t");
			ctx.output.append(indent);
			ctx.output.append("}\n");
			return returns;
		};
	}
}
