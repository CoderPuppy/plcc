package myplcc.lexer;

import myplcc.ClassRef;
import myplcc.GeneratedClass;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;

public class Terminals {
	public final GeneratedClass generatedClass;
	public final LinkedHashMap<String, Terminal> terminals = new LinkedHashMap<>();
	public final Terminal EOF = new Terminal(this, "$EOF", "null", false);
	public final Terminal ERROR = new Terminal(this, "$ERROR", "null", false);

	public static final ClassRef iTerminal = ClassRef.runtime("ITerminal");
	public static final ClassRef pattern = new ClassRef(
		Arrays.asList("java", "util", "regex"),
		Collections.singletonList("Pattern"));

	public Terminals(GeneratedClass generatedClass) {
		assert generatedClass.type == GeneratedClass.Type.ENUM;
		this.generatedClass = generatedClass;
		assert generatedClass.generators.isEmpty();
		generatedClass.generators.add(this::generate);
		generatedClass.addInterface(iTerminal);
		generatedClass.addImport(iTerminal);
		generatedClass.addImport(pattern);
	}

	private void generate(String indent, Appendable output) throws IOException {
		boolean sep = false;
		for(Terminal t : terminals.values()) {
			if(sep) output.append(",\n");
			sep = true;
			output.append(indent);
			output.append(t.name);
			output.append('(');
			output.append(t.pattern);
			if(t.skip) {
				output.append(", true");
			}
			output.append(")");
		}
		output.append(";\n");

		output.append("\n");
		output.append(indent);
		output.append("public String pattern;\n");
		output.append(indent);
		output.append("public boolean skip;\n");
		output.append(indent);
		output.append("public Pattern cPattern;\n");

		output.append("\n");
		output.append(indent);
		output.append(generatedClass.classRef.getName());
		output.append("(String pattern, boolean skip) {\n");
		output.append(indent);
		output.append("\tthis.pattern = pattern;\n");
		output.append(indent);
		output.append("\tthis.skip = skip;\n");
		output.append(indent);
		output.append("\tif(pattern != null)\n");
		output.append(indent);
		output.append("\t\tthis.cPattern = Pattern.compile(pattern, Pattern.DOTALL);\n");
		output.append(indent);
		output.append("}\n");

		output.append(indent);
		output.append(generatedClass.classRef.getName());
		output.append("(String pattern) {\n");
		output.append(indent);
		output.append("\tthis(pattern, false);\n");
		output.append(indent);
		output.append("}\n");

		output.append("\n");

		output.append(indent);
		output.append("@Override\n");
		output.append(indent);
		output.append("public boolean isError() {\n");
		output.append(indent);
		output.append("\treturn this == $ERROR;\n");
		output.append(indent);
		output.append("}\n");

		output.append(indent);
		output.append("@Override\n");
		output.append(indent);
		output.append("public boolean isEOF() {\n");
		output.append(indent);
		output.append("\treturn this == $EOF;\n");
		output.append(indent);
		output.append("}\n");

		output.append(indent);
		output.append("@Override\n");
		output.append(indent);
		output.append("public Pattern getCompiledPattern() {\n");
		output.append(indent);
		output.append("\treturn cPattern;\n");
		output.append(indent);
		output.append("}\n");

		output.append(indent);
		output.append("@Override\n");
		output.append(indent);
		output.append("public String getPattern() {\n");
		output.append(indent);
		output.append("\treturn pattern;\n");
		output.append(indent);
		output.append("}\n");

		output.append(indent);
		output.append("@Override\n");
		output.append(indent);
		output.append("public boolean isSkip() {\n");
		output.append(indent);
		output.append("\treturn skip;\n");
		output.append(indent);
		output.append("}\n");
	}
}
