import java.util.regex.Pattern;
interface ITerminal {
	String getPattern();
	boolean isSkip();
	Pattern getCompiledPattern();
	boolean isEOF();
	boolean isError();
}
