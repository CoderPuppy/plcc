package myplcc;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class DataClass implements Generator {
	public final GeneratedClass generatedClass;
	public final Map<String, TypeRef> fields;
	public final List<Generator> constructorGens = new ArrayList<>();

	public DataClass(GeneratedClass generatedClass, Map<String, TypeRef> fields) {
		assert generatedClass.type == GeneratedClass.Type.CLASS;
		this.generatedClass = generatedClass;
		this.fields = fields;
		generatedClass.generators.add(this);
		for(TypeRef typeRef : fields.values())
			typeRef.addImports(generatedClass::addImport);
	}

	@Override
	public void generate(String indent, Appendable output) throws IOException {
		for(Map.Entry<String, TypeRef> field : fields.entrySet()) {
			output.append(indent);
			output.append("public ");
			// TODO: final
			field.getValue().generate(output);
			output.append(" ");
			output.append(field.getKey());
			output.append(";\n");
		}
		if(!fields.isEmpty())
			output.append("\n");

		output.append(indent);
		output.append("public ");
		output.append(generatedClass.classRef.getName());
		output.append("(");
		boolean sep = false;
		for(Map.Entry<String, TypeRef> field : fields.entrySet()) {
			if(sep)
				output.append(", ");
			sep = true;
			field.getValue().generate(output);
			output.append(" ");
			output.append(field.getKey());
		}
		output.append(") {\n");
		for(Map.Entry<String, TypeRef> field : fields.entrySet()) {
			output.append(indent);
			output.append("\tthis.");
			output.append(field.getKey());
			output.append(" = ");
			output.append(field.getKey());
			output.append(";\n");
		}
		for(Generator gen : constructorGens) {
			gen.generate(indent + "\t", output);
		}
		output.append(indent);
		output.append("}\n");
	}
}
