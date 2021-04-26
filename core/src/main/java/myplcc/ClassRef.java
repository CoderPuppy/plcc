package myplcc;

import java.io.IOException;
import java.util.*;

public class ClassRef {
	public final List<String> packageParts;
	public final List<String> classParts;

	public ClassRef(List<String> packageParts, List<String> classParts) {
		this.packageParts = packageParts;
		this.classParts = classParts;
	}

	public void generatePackage(CharSequence sep, Appendable output) throws IOException {
		for(String part : packageParts) {
			output.append(part);
			output.append(sep);
		}
	}

	public void generateCls(Appendable output) throws IOException {
		generateCls(".", output);
	}

	public void generateCls(CharSequence sep, Appendable output) throws IOException {
		boolean first = true;
		for(String part : classParts) {
			if(!first)
				output.append(sep);
			first = false;
			output.append(part);
		}
	}

	public String getCls() {
		StringBuilder sb = new StringBuilder();
		try {
			generateCls(".", sb);
		} catch(IOException e) {
			// this should never happen, because StringBuilder doesn't throw IOExceptions
			throw new RuntimeException(e);
		}
		return sb.toString();
	}

	public void generate(Appendable output) throws IOException {
		generate(".", output);
	}

	public void generate(CharSequence sep, Appendable output) throws IOException {
		generatePackage(sep, output);
		generateCls(sep, output);
	}

	public String getName() {
		return classParts.get(classParts.size() - 1);
	}

	public TypeRef typeRef() {
		return new TypeRef.Class(this);
	}

	public ClassRef nested(String... name) {
		List<String> classParts = new ArrayList<>(this.classParts);
		Collections.addAll(classParts, name);
		return new ClassRef(packageParts, classParts);
	}

	@Override
	public String toString() {
		StringBuilder sb = new StringBuilder();
		try {
			generate(sb);
		} catch(IOException e) {
			// this should never happen because StringBuilder doesn't throw IOException
			throw new RuntimeException(e);
		}
		return sb.toString();
	}

	public static final List<String> runtimePkg = Arrays.asList("myplcc", "runtime");
	public static final List<String> langPkg = Arrays.asList("java", "lang");
	public static final List<String> utilPkg = Arrays.asList("java", "util");

	public static ClassRef runtime(String... name) {
		return new ClassRef(runtimePkg, Arrays.asList(name));
	}

	public static ClassRef lang(String... name) {
		return new ClassRef(langPkg, Arrays.asList(name));
	}

	public static ClassRef util(String... name) {
		return new ClassRef(utilPkg, Arrays.asList(name));
	}

	@Override
	public boolean equals(Object o) {
		if(this == o) return true;
		if(o == null || getClass() != o.getClass()) return false;
		ClassRef classRef = (ClassRef) o;
		return Objects.equals(packageParts, classRef.packageParts) && Objects.equals(classParts, classRef.classParts);
	}

	@Override
	public int hashCode() {
		return Objects.hash(packageParts, classParts);
	}
}
