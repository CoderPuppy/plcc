package myplcc;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.io.BufferedReader;
import java.io.StringReader;
import java.io.IOException;

public class Scan<T extends ITerminal> {
	private BufferedReader reader;
	private String line = null; // line buffer
	private int place; // current index in `line`
	private int lineNum = 0;
	private Token<T> tok = null;

	private T[] terminals;
	private T eofTerminal;
	private T errorTerminal;

	public Scan(T[] terminals, T eofTerminal, T errorTerminal, BufferedReader reader) {
		this.terminals = terminals;
		this.eofTerminal = eofTerminal;
		this.errorTerminal = errorTerminal;
		this.reader = reader;
	}
	public Scan(T[] terminals, T eofTerminal, T errorTerminal, String s) {
		this(terminals, eofTerminal, errorTerminal, new BufferedReader(new StringReader(s)));
	}

	public void fillString() {
		if(line == null | place >= line.length()) {
			try {
				line = reader.readLine();
				if(line == null)
					return; // EOF
				lineNum++;
				line += "\n";
				place = 0;
			} catch(IOException e) {
				line = null;
			}
		}
	}
	public Token<T> cur() {
		if(tok != null)
			return tok;

		String longestString = "";
		T longestTerminal = null;

LOOP:
		while(true) {
			fillString();
			if(line == null) {
				tok = new Token<T>(eofTerminal, "EOF", lineNum);
				return tok;
			}
			int longestEnd = place;
			for(T terminal : terminals) {
				Pattern pat = terminal.getCompiledPattern();
				if(pat == null)
					break;
				if(terminal.isSkip() && longestTerminal != null)
					continue; // already have a match, just looking for a longer one, can't skip
				Matcher m = pat.matcher(line);
				m.region(place, line.length());
				if(m.lookingAt()) {
					int end = m.end();
					if(end == place)
						continue; // matched nothing
					if(terminal.isSkip()) {
						place = end;
						continue LOOP;
					}
					if(longestEnd < end) {
						longestEnd = end;
						longestString = m.group();
						longestTerminal = terminal;
					}
				}
			}
			if(longestTerminal == null) {
				char c = line.charAt(place);
				String str;
				if(c >= ' ' && c <= '~')
					str = String.format("%c", c);
				else
					str = String.format("\\u%04x", (int)c);
				tok = new Token<T>(errorTerminal, str, lineNum);
				place += 1;
				return tok;
			}
			place = longestEnd;
			tok = new Token<T>(longestTerminal, longestString, lineNum);
			return tok;
		}
	}
	public void adv() {
		if(tok == null)
			cur();
		tok = null;
	}
	public Token<T> match(T terminal, ITrace<T> trace) {
		Token<T> t = cur();
		if(t.terminal == terminal) {
			if(trace != null)
				trace.print(t);
			adv();
		} else {
			throw new RuntimeException("match failure: expected token " + terminal + ", got " + t);
		}
		return t;
	}
}
