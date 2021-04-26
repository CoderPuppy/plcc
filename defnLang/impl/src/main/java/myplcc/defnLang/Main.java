package myplcc.defnLang;

import myplcc.runtime.CLI;

public class Main extends CLI<Terminal, Item> {
	public Main() {
		super(Terminal.set, Program::parse);
	}

	public static void main(String[] args) {
		new Main().run(args);
	}
}
