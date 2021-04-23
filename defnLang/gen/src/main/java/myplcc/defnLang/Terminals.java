package myplcc.defnLang;

import myplcc.runtime.ITerminal;
import java.util.regex.Pattern;

public enum Terminals implements ITerminal {
	$EOF(null),
	$ERROR(null),
	WHITESPACE("[ \u0005c]+"),
	NEWLINE("\u0000d\u0000a\u0000d\u0000a"),
	TOKEN("token"),
	TERMINALS("terminals"),
	DOT("\u0005c"),
	TERMINAL_NAME("[A-Z][A-Z\u0005c_]*"),
	NONTERM_NAME("[a-z]\u0005c*"),
	LANGLE("<"),
	RANGLE(">"),
	RULE_DEF("::="),
	REPEATING_RULE_DEF("\u0005c\u0005c="),
	IDENT("(?!\u0005c)\u0005c+"),
	STR("\u00022?:[^\u00022\u0005c\u0005c|\u0005c)\u00022"),
	RAW_STR("'(?:[^'\u0005c\u0005c|\u0005c)'"),
	EXTRA_CODE_SEP("%%%%*"),
	COMMENT("#");

	public String pattern;
	public boolean skip;
	public Pattern cPattern;

	Terminals(String pattern, boolean skip) {
		this.pattern = pattern;
		this.skip = skip;
		if(pattern != null)
			this.cPattern = Pattern.compile(pattern, Pattern.DOTALL);
	}
	Terminals(String pattern) {
		this(pattern, false);
	}

	@Override
	public boolean isError() {
		return this == $ERROR;
	}
	@Override
	public boolean isEOF() {
		return this == $EOF;
	}
	@Override
	public Pattern getCompiledPattern() {
		return cPattern;
	}
	@Override
	public String getPattern() {
		return pattern;
	}
	@Override
	public boolean isSkip() {
		return skip;
	}
}
