package myplcc;

import java.util.regex.Pattern;

public interface ITerminal {
	String getPattern();
	boolean isSkip();
	Pattern getCompiledPattern();
	boolean isEOF();
	boolean isError();

	public static final class Set<T> {
		public final T[] values;
		public final T eof;
		public final T error;

		public Set(T[] values, T eof, T error) {
			this.values = values;
			this.eof = eof;
			this.error = error;
		}
	}
}
