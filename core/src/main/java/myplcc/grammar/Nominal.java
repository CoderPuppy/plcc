package myplcc.grammar;

import myplcc.ClassRef;
import myplcc.GeneratedClass;
import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.io.IOException;
import java.util.Set;
import java.util.function.Consumer;

public class Nominal implements Element, Generator {
	public final GeneratedClass generatedClass;
	public final Element element;
	public final String methodName;

	public Nominal(GeneratedClass generatedClass, Element element) {
		this(generatedClass, "parse", element);
	}

	public Nominal(GeneratedClass generatedClass, String methodName, Element element) {
		this.generatedClass = generatedClass;
		this.element = element;
		this.methodName = methodName;
		generatedClass.generators.add(this);
		generatedClass.addImport(getTerminals().generatedClass.classRef);
		element.addImports(generatedClass::addImport);
	}

	@Override
	public void generate(String indent, Appendable output) throws IOException {
		output.append(indent);
		output.append("public static ");
		getOutputType().generate(output);
		output.append(" ");
		output.append(methodName);
		output.append("(myplcc.runtime.Scan<");
		getTerminals().generatedClass.classRef.generateCls(output);
		output.append("> scan$, myplcc.runtime.ITrace<");
		getTerminals().generatedClass.classRef.generateCls(output);
		output.append("> trace$");
		if(hasSeparator()) output.append(", myplcc.runtime.ExplicitRepCtx repCtx$");
		output.append(") {\n");
		Generator.MethodContext ctx = new Generator.MethodContext(output);

		boolean returns = element.generateParse((expr, required) -> (ctx1, indent1) -> {
			ctx1.output.append(indent1);
			ctx1.output.append("return ");
			ctx1.output.append(expr);
			ctx1.output.append(";\n");
			return false;
		}, hasSeparator() ? "repCtx$" : null).generate(ctx, indent + "\t");
		if(returns) {
			output.append(indent);
			output.append("\tthrow new RuntimeException(\"TODO: bad\");\n");
		}

		output.append(indent);
		output.append("}\n");
	}

	@Override
	public Generator.Method generateParse(Generator.ExprSink after, String explicitRepCtx) {
		return (ctx, indent) -> {
			StringBuilder builder = new StringBuilder();
			generatedClass.classRef.generateCls(builder);
			builder.append(".");
			builder.append(methodName);
			builder.append("(scan$, trace$");
			if(hasSeparator()) {
				builder.append(", ");
				builder.append(explicitRepCtx);
			}
			builder.append(")");
			return after.withExpr(builder.toString(), true).generate(ctx, indent);
		};
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
		element.checkLL1();
	}

	@Override
	public boolean hasSeparator() {
		return element.hasSeparator();
	}

	@Override
	public Terminals getTerminals() {
		return element.getTerminals();
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		Element.super.addImports(doImport);
		doImport.accept(generatedClass.classRef);
	}
}
