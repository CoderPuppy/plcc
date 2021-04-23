package myplcc.grammar;

import myplcc.ClassRef;
import myplcc.Generator;
import myplcc.TypeRef;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.util.Set;
import java.util.function.Consumer;

public interface Element {
	Set<Terminal> getFirstSet();

	boolean isPossiblyEmpty();

	default void checkLL1() {
	}

	default boolean hasSeparator() {
		return false;
	}

	TypeRef getOutputType();

	Terminals getTerminals();

	Generator.Method generateParse(Generator.ExprSink after, String explicitRepCtx);

	default void addImports(Consumer<ClassRef> doImport) {
		getOutputType().addImports(doImport);
	}
}
