package myplcc;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

public class Visitor {
	public final GeneratedClass superclass;
	public final GeneratedClass generatedClass;
	public final Set<GeneratedClass> subclasses = new HashSet<>();

	public Visitor(GeneratedClass superclass, GeneratedClass generatedClass) {
		this.superclass = superclass;
		this.generatedClass = generatedClass;
		assert generatedClass.type == GeneratedClass.Type.INTERFACE;
		superclass.generators.add(this::generateSuper);
		superclass.addImport(generatedClass.classRef);
		generatedClass.generators.add(this::generateIface);
		generatedClass.setCustomHead(this::generateIfaceHead);
	}

	public Visitor(GeneratedClass superclass) {
		this(superclass, new GeneratedClass("Visitor", GeneratedClass.Type.INTERFACE, superclass));
	}

	public void addSubclass(GeneratedClass subclass) {
		subclasses.add(subclass);
		subclass.addImport(generatedClass.classRef);
		subclass.generators.add(new Subclass(subclass));
	}

	public void generateSuper(String indent, Appendable output) throws IOException {
		output.append(indent);
		output.append("public abstract <T> T visit(");
		generatedClass.classRef.generateCls(output);
		output.append("<T> visitor);\n");
	}

	public void generateIfaceHead(String indent, Appendable output) throws IOException {
		output.append(indent);
		output.append("public interface ");
		output.append(generatedClass.classRef.getName());
		output.append("<T> {\n");
	}

	public void generateIface(String indent, Appendable output) throws IOException {
		for(GeneratedClass subclass : subclasses) {
			output.append(indent);
			output.append("T visit");
			output.append(subclass.classRef.getName());
			output.append("(");
			subclass.classRef.generateCls(output);
			output.append(" o);\n");
		}
	}

	private class Subclass implements Generator {
		public final GeneratedClass subclass;

		public Subclass(GeneratedClass subclass) {
			this.subclass = subclass;
		}

		@Override
		public void generate(String indent, Appendable output) throws IOException {
			output.append(indent);
			output.append("@Override\n");
			output.append(indent);
			output.append("public <T> T visit(");
			generatedClass.classRef.generateCls(output);
			output.append("<T> visitor) {\n");
			output.append(indent);
			output.append("\treturn visitor.visit");
			output.append(subclass.classRef.getName());
			output.append("(this);\n");
			output.append(indent);
			output.append("}\n");
		}
	}
}
