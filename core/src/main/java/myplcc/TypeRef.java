package myplcc;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.Set;
import java.util.function.Consumer;

public interface TypeRef {
	default void addImports(Consumer<ClassRef> doImport) {
	}

	void generate(Appendable output) throws IOException;

	class Class implements TypeRef {
		public final ClassRef classRef;

		public Class(ClassRef classRef) {
			this.classRef = classRef;
		}

		@Override
		public void addImports(Consumer<ClassRef> doImport) {
			doImport.accept(classRef);
		}

		@Override
		public void generate(Appendable output) throws IOException {
			classRef.generateCls(output);
		}
	}

	class List implements TypeRef {
		public final TypeRef element;

		public List(TypeRef element) {
			this.element = element;
		}

		private static final ClassRef list = ClassRef.util("List");

		@Override
		public void addImports(Consumer<ClassRef> doImport) {
			element.addImports(doImport);
			doImport.accept(list);
		}

		@Override
		public void generate(Appendable output) throws IOException {
			output.append("List<");
			element.generate(output);
			output.append('>');
		}
	}
}
