package myplcc.lexer;

import myplcc.ClassRef;

import java.io.IOException;
import java.util.Set;
import java.util.function.Consumer;

public class GenericToken implements Token {
	public final Terminals terminals;

	public GenericToken(Terminals terminals) {
		this.terminals = terminals;
	}

	@Override
	public void generate(Appendable output) throws IOException {
		output.append("myplcc.runtime.Token<");
		terminals.generatedClass.classRef.generateCls(output);
		output.append(">");
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		doImport.accept(terminals.generatedClass.classRef);
	}

	@Override
	public Terminals getTerminals() {
		return terminals;
	}
}
