package myplcc;

import java.util.regex.Pattern;

public interface ITerminal {
	String getPattern();
	boolean isSkip();
	Pattern getCompiledPattern();
	boolean isEOF();
	boolean isError();
}
