package myplcc;

import java.io.IOException;
import java.util.*;
import java.util.stream.Stream;

public class GeneratedClass implements Generator {
	public final ClassRef classRef;
	public final Type type;
	public final List<Generator> generators = new ArrayList<>();
	private ClassRef superclass = null;
	private final Set<ClassRef> interfaces = new HashSet<>();
	private final Map<String, ClassRef> imports;
	public final GeneratedClass enclosingClass;
	private boolean isAbstract = false;
	private Generator headGenerator = null;

	public GeneratedClass(ClassRef classRef, Type type, GeneratedClass enclosingClass) {
		this.classRef = classRef;
		this.type = type;
		this.enclosingClass = enclosingClass;
		if(enclosingClass == null) {
			imports = new HashMap<>();
		} else {
			enclosingClass.generators.add(this);
			imports = enclosingClass.imports;
		}
	}

	public GeneratedClass(ClassRef classRef, Type type) {
		this(classRef, type, null);
	}

	public GeneratedClass(String name, Type type, GeneratedClass enclosingClass) {
		this(enclosingClass.classRef.nested(name), type, enclosingClass);
	}

	public void addImport(ClassRef ref) {
		assert !imports.containsKey(ref.getCls());
		imports.put(ref.getCls(), ref);
	}

	public void addInterface(ClassRef ref) {
		interfaces.add(ref);
		addImport(ref);
	}

	public ClassRef getSuperclass() {
		return superclass;
	}

	public void setSuperclass(ClassRef superclass) {
		assert this.superclass == null;
		assert type == Type.CLASS;
		this.superclass = superclass;
		addImport(superclass);
	}

	public void makeAbstract() {
		assert type == Type.CLASS;
		isAbstract = true;
	}

	public void setCustomHead(Generator headGenerator) {
		assert this.headGenerator == null;
		this.headGenerator = headGenerator;
	}

	@Override
	public void generate(String indent, Appendable output) throws IOException {
		if(enclosingClass == null) {
			assert indent.isEmpty();
			if(!classRef.packageParts.isEmpty()) {
				output.append("package ");
				boolean sep = false;
				for(String part : classRef.packageParts) {
					if(sep) output.append('.');
					output.append(part);
					sep = true;
				}
				output.append(";\n\n");
			}
			boolean any = false;
			for(ClassRef ref : imports.values()) {
				if(ref.packageParts.equals(classRef.packageParts))
					continue;
				output.append("import ");
				ref.generate(output);
				output.append(";\n");
				any = true;
			}
			if(any) output.append('\n');
		}

		if(headGenerator != null)
			headGenerator.generate(indent, output);
		else {
			output.append(indent);
			output.append("public ");
			if(enclosingClass != null)
				output.append("static ");
			if(isAbstract)
				output.append("abstract ");
			output.append(type.name().toLowerCase());
			output.append(' ');
			output.append(classRef.getName());
			if(superclass != null && type == Type.CLASS) {
				output.append(" extends ");
				superclass.generateCls(output);
			}
			if(!interfaces.isEmpty()) {
				if(type == Type.INTERFACE)
					output.append(" extends ");
				else
					output.append(" implements ");
				boolean sep = false;
				for(ClassRef ref : interfaces) {
					if(sep)
						output.append(", ");
					sep = true;
					ref.generateCls(output);
				}
			}
			output.append(" {\n");
		}

		boolean first = true;
		for(Generator g : generators) {
			if(!first)
				output.append("\n");
			first = false;
			g.generate(indent + "\t", output);
		}

		output.append(indent);
		output.append("}\n");
	}

	public enum Type {
		CLASS, INTERFACE, ENUM;
	}
}
