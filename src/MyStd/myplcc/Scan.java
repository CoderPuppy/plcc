package myplcc;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.io.BufferedReader;
import java.io.StringReader;
import java.io.IOException;

public class Scan<T extends ITerminal> {
	private BufferedReader rdr;
	private String s;
	private int start;
	private int end;

	private int lno;
	private Token<T> tok;

	private T[] terminals;
	private T eofTerminal;
	private T errorTerminal;

	public Scan(T[] terminals, T eofTerminal, T errorTerminal, BufferedReader rdr) {
		this.terminals = terminals;
		this.eofTerminal = eofTerminal;
		this.errorTerminal = errorTerminal;
		this.rdr = rdr;
		this.lno = 0;
		s = null;
		tok = null;
	}
	public Scan(T[] terminals, T eofTerminal, T errorTerminal, String s) {
		this(terminals, eofTerminal, errorTerminal, new BufferedReader(new StringReader(s)));
	}

	public void fillString() {
		if(s == null | start >= end) {
			try {
				s = rdr.readLine();
				if(s == null)
					return;
				lno++;
				s += "\n";
				start = 0;
				end = s.length();
			} catch(IOException e) {
				s = null;
			}
		}
	}
	public Token<T> cur() {
		if(tok != null)
			return tok;

		String matchString = "";
		T terminalFound = null;

LOOP:
		while(true) {
			fillString();
			if(s == null) {
				tok = new Token<T>(eofTerminal, "EOF", lno);
				return tok;
			}
			int matchEnd = start;
			for(T terminal : terminals) {
				Pattern pat = terminal.getCompiledPattern();
				if(pat == null)
					break;
				if(terminal.isSkip() && terminalFound != null)
					continue;
				Matcher m = pat.matcher(s);
				m.region(start, end);
				if(m.lookingAt()) {
					int e = m.end();
					if(e == start)
						continue;
					if(terminal.isSkip()) {
						start = e;
						continue LOOP;
					}
					if(matchEnd < e) {
						matchEnd = e;
						matchString = m.group();
						terminalFound = terminal;
					}
				}
			}
			if(terminalFound == null) {
				char ch = s.charAt(start++);
				String sch;
				if(ch >= ' ' && ch <= '~')
					sch = String.format("%c", ch);
				else
					sch = String.format("\\u%04x", (int)ch);
				tok = new Token<T>(errorTerminal, sch, lno);
				return tok;
			}
			start = matchEnd;
			tok = new Token<T>(terminalFound, matchString, lno);
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
