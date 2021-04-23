package myplcc.lexer;

import myplcc.ClassRef;
import myplcc.GeneratedClass;

import java.io.IOException;
import java.util.Set;
import java.util.function.Consumer;

public class CompatToken implements Token {
	public final GeneratedClass generatedClass;
	public final Terminals terminals;

	public CompatToken(GeneratedClass generatedClass, Terminals terminals) {
		this.generatedClass = generatedClass;
		this.terminals = terminals;
		generatedClass.generators.add(this::generate);
		generatedClass.addImport(terminals.generatedClass.classRef);
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		doImport.accept(generatedClass.classRef);
	}

	@Override
	public Terminals getTerminals() {
		return terminals;
	}

	@Override
	public void generate(Appendable output) throws IOException {
		generatedClass.classRef.generateCls(output);
	}

	private void generate(String indent, Appendable output) throws IOException {
		output.append(indent);
		output.append("public ");
		terminals.generatedClass.classRef.generateCls(output);
		output.append(" val;\n");
		output.append(indent);
		output.append("public String str;\n");
		output.append(indent);
		output.append("public int lno;\n");
		// TODO
	}
}
