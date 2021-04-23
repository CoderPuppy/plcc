package myplcc.runtime;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.List;

public abstract class CLI<T extends ITerminal, R> {
	public final ITerminal.Set<T> terminals;
	public final IParse<T, R> parser;
	public ITrace<T> trace = null;
	public List<String> files = new ArrayList<String>();
	public String prompt = "--> ";
	public enum Mode { Parse, Scan }
	public Mode mode = Mode.Parse;

	public CLI(ITerminal.Set<T> terminals, IParse<T, R> parser) {
		this.terminals = terminals;
		this.parser = parser;
	}

	public void run(String[] args) {
		processArgs(args);
		for(String file : files) {
			try {
				processSrc(new BufferedReader(new FileReader(file)), null);
			} catch(FileNotFoundException ex) {
				System.err.println(file + ": no such file");
				System.exit(1);
			}
		}
		processSrc(new BufferedReader(new InputStreamReader(System.in)), System.out);
	}

	public void processArgs(String[] args) {
		boolean enableOpts = true;
		for(String arg : args) {
			if(enableOpts) {
				if(arg.equals("--")) {
					enableOpts = false;
					continue;
				} else if(processOpt(arg)) {
					continue;
				}
			}
			files.add(arg);
		}
	}

	public boolean processOpt(String arg) {
		switch(arg) {
			// "--" is handled in processArgs, because it needs to set enableOpts
			case "-p":
			case "--parse":
				mode = Mode.Parse;
				return true;
			case "-s":
			case "--scan":
				mode = Mode.Scan;
				// fallthrough to "-t", "--trace"
			case "-t":
			case "--trace":
				trace = new PrintTrace<T>(System.out);
				return true;
			case "--no-trace":
				trace = null;
				return true;
			case "-n":
			case "--no-prompt":
				prompt = "";
				return true;
			default:
				return false;
		}
	}

	public void processSrc(BufferedReader reader, PrintStream replOut) {
		Scan<T> scan = new Scan<T>(terminals, reader, 0);
		if(trace != null)
			trace.reset();
		if(mode == Mode.Parse) {
			while(true) {
				if(replOut != null)
					replOut.print(prompt);
				if(scan.getCurrentToken().isEOF())
					break;
				while(scan.hasBuffer()) {
					try {
						R result = parser.parse(scan, trace);
						processResult(result);
					} catch(RuntimeException ex) {
						if(replOut == null)
							throw ex;
						else {
							ex.printStackTrace();
							scan.empty();
						}
					}
				}
			}
		} else if(mode == Mode.Scan) {
			while(true) {
				if(replOut != null)
					replOut.print(prompt);
				if(scan.getCurrentToken().isEOF())
					break;
				System.out.println(scan.getCurrentToken());
				while(scan.hasBuffer()) {
					Token<T> token = scan.getCurrentToken();
					if(trace != null)
						trace.print(token);
					scan.next();
				}
			}
		}
	}

	public void processResult(R result) {
		System.out.println(result);
	}
}
