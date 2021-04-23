package myplcc;

import java.io.IOException;
import java.util.List;

public interface Generator {
	void generate(String indent, Appendable output) throws IOException;

	interface Method {
		boolean generate(MethodContext ctx, String indent) throws IOException;
	}

	interface ExprSink {
		Method withExpr(String expr, boolean required);
	}

	class MethodContext {
		public final Appendable output;
		public int suffix = 0;

		public MethodContext(Appendable output) {
			this.output = output;
		}
	}
}
