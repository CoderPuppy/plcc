package myplcc.runtime;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.io.BufferedReader;
import java.io.IOException;

public class Scan<T extends ITerminal> {
	private BufferedReader reader;
	private String line = null; // line buffer
	private int place; // current index in `line`
	private int lineNum;
	private Token<T> tok = null;
	private Token<T> peekTok = null;

	private ITerminal.Set<T> terminals;

	public Scan(ITerminal.Set<T> terminals, BufferedReader reader, int lineNum) {
		this.terminals = terminals;
		this.reader = reader;
		this.lineNum = lineNum;
	}

	public void empty() {
		line = null;
		tok = null;
	}
	public boolean hasBuffer() {
		return (line != null && place < line.length()) || tok != null || peekTok != null;
	}
	private void fillString() {
		if(line != null && place < line.length())
			return;
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
	private Token<T> peek(boolean fill) {
		String longestString = "";
		T longestTerminal = null;

		LOOP:
		while(true) {
			if(fill)
				fillString();
			else if(line == null || place >= line.length())
				return null;
			if(line == null) {
				return new Token<T>(terminals.eof, "EOF", lineNum);
			}
			int longestEnd = place;
			for(T terminal : terminals.values) {
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
				place += 1;
				return new Token<T>(terminals.error, str, lineNum);
			}
			place = longestEnd;
			return new Token<T>(longestTerminal, longestString, lineNum);
		}
	}
	public Token<T> getCurrentToken() {
		if(tok != null)
			return tok;
		if(peekTok != null) {
			tok = peekTok;
			peekTok = peek(false);
			return tok;
		}
		tok = peek(true);
		peekTok = peek(false);
		return tok;
	}
	public void next() {
		if(tok == null)
			getCurrentToken();
		tok = null;
	}
	public Token<T> take(ITrace<T> trace) {
		Token<T> t = getCurrentToken();
		if(trace != null)
			trace.print(t);
		next();
		return t;
	}
	public Token<T> match(T terminal, ITrace<T> trace) {
		Token<T> t = getCurrentToken();
		if(t.terminal == terminal) {
			if(trace != null)
				trace.print(t);
			next();
		} else {
			throw new RuntimeException("match failure: expected token " + terminal + ", got " + t);
		}
		return t;
	}
	public int getLineNumber() {
		return lineNum;
	}
}
