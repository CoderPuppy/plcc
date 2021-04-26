package myplcc.defnLang;

import myplcc.*;
import myplcc.grammar.*;
import myplcc.lexer.GenericToken;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.util.*;

public final class DefinitionLanguage {
	public static final List<String> pkg = Arrays.asList("myplcc", "defnLang");
	public static final Map<String, GeneratedClass> generatedClasses = new HashMap<>();

	private static GeneratedClass generateClass(String name, GeneratedClass.Type type) {
		assert !generatedClasses.containsKey(name);
		GeneratedClass generatedClass = new GeneratedClass(new ClassRef(pkg, Collections.singletonList(name)), type);
		generatedClasses.put(name, generatedClass);
		return generatedClass;
	}

	public static final Terminals terminals = new Terminals(generateClass("Terminals", GeneratedClass.Type.ENUM));
	public static final GenericToken token = new GenericToken(terminals);

	private static Terminal terminal(String name, String pat) {
		return new Terminal(terminals, name, Utils.escapeString(pat), false);
	}

	public static final Terminal WHITESPACE = terminal("WHITESPACE", "[ \t]+");
	public static final Terminal NEWLINE = terminal("NEWLINE", "\r\n|\r|\n");
	public static final Terminal TOKEN = terminal("TOKEN", "token");
	public static final Terminal TERMINALS = terminal("TERMINALS", "terminals");
	public static final Terminal DOT = terminal("DOT", "\\.");
	public static final Terminal TERMiNAL_NAME = terminal("TERMINAL_NAME", "[A-Z][A-Z\\d_]*");
	public static final Terminal NONTERM_NAME = terminal("NONTERM_NAME", "[a-z]\\w*");
	public static final Terminal LANGLE = terminal("LANGLE", "<");
	public static final Terminal RANGLE = terminal("RANGLE", ">");
	public static final Terminal RULE_DEF = terminal("RULE_DEF", "::=");
	public static final Terminal REPEATING_RULE_DEF = terminal("REPEATING_RULE_DEF", "\\*\\*=");
	public static final Terminal IDENT = terminal("IDENT", "(?!\\d)\\w+");
	public static final Terminal STR = terminal("STR", "\"(?:[^\"\\\\]|\\\\.)*\"");
	public static final Terminal RAW_STR = terminal("RAW_STR", "'(?:[^'\\\\]|\\\\.)*'");
	public static final Terminal EXTRA_CODE_SEP = terminal("EXTRA_CODE_SEP", "%%%%*");
	public static final Terminal COMMENT = terminal("COMMENT", "#");

	public static final GeneratedClass helperRules = generateClass("HelperRules", GeneratedClass.Type.CLASS);
	public static final Nominal whitespaceRule = new Nominal(helperRules, "whitespace",
		new Context("whitespace",
			new Repeated(new TerminalClass(token, WHITESPACE), 0, null)
		)
	);
	public static final Nominal blankLineRule = new Nominal(helperRules, "blankLine",
		new Context("blankLink", new Compound(
			output -> output.append("Object"),
			after -> after.withExpr("null", false),
			new Compound.Item(null, whitespaceRule),
			new Compound.Item(null, new Repeated(new Compound(
				output -> output.append("Object"),
				after -> after.withExpr("null", false),
				new Compound.Item(null, new TerminalClass(token, COMMENT)),
				new Compound.Item(null, new Repeated(
					new TerminalClass(token, Utils.setDifference(terminals.terminals.values(), Collections.singletonList(NEWLINE))),
					0, null
				))
			), 0, 1)),
			new Compound.Item(null, new TerminalClass(token, NEWLINE, terminals.EOF))
		))
	);
	public static final Nominal nontermNameRule = new Nominal(helperRules, "nontermName",
		new Context("nontermName",
			new TerminalClass(token, NONTERM_NAME, TOKEN, TERMINALS)
		)
	);
	public static final Nominal javaIdentRule = new Nominal(helperRules, "javaIdent",
		new Context("javaIdent",
			new TerminalClass(token, TERMiNAL_NAME, NONTERM_NAME, IDENT, TOKEN, TERMINALS)
		)
	);
	public static final Nominal javaPathIdentRule = new Nominal(helperRules, "javaPathIdent",
		new Context("javaPathIdent",
			new TerminalClass(token, NONTERM_NAME, IDENT)
		)
	);
	public static final Nominal javaPathRule = new Nominal(helperRules, "javaPath",
		new Context("javaPath", new Repeated(new Compound(
			token, after -> after.withExpr("part", false),
			new Compound.Item("part", javaPathIdentRule),
			new Compound.Item(null, new Separator(new TerminalClass(token, DOT)))
		), 1, null))
	);

	public static final Compound.Class terminalsRule = new Compound.Class(
		generateClass("TerminalsRule", GeneratedClass.Type.CLASS),
		"terminals",
		new Compound.Item(null, new TerminalClass(token, TERMINALS)),
		new Compound.Item(null, whitespaceRule),
		new Compound.Item("path", javaPathRule)
	);
	public static final Compound.Class tokenRule = new Compound.Class(
		generateClass("TokenRule", GeneratedClass.Type.CLASS),
		"token",
		new Compound.Item("tokenType",
			new Compound(
				terminals.generatedClass.classRef.typeRef(),
				after -> after.withExpr("tokenTypeList.isEmpty() ? " +
					terminals.generatedClass.classRef.getCls() + "." + TOKEN.name +
					" : tokenTypeList.get(0).terminal", false),
				new Compound.Item("tokenTypeList", new Repeated(new Compound(
					token,
					after -> after.withExpr("token", false),
					new Compound.Item("token", new TerminalClass(token, TOKEN)),
					new Compound.Item(null, whitespaceRule)
				), 0, 1))
			)),
		new Compound.Item("name", new TerminalClass(token, TERMiNAL_NAME)),
		new Compound.Item(null, whitespaceRule),
		new Compound.Item("pattern", new TerminalClass(token, STR, RAW_STR))
	);
	public static final Compound.Class nontermItemRule = new Compound.Class(
		generateClass("NontermItemRule", GeneratedClass.Type.CLASS),
		"nontermItem",
		new Compound.Item(null, whitespaceRule)
		// TODO
	);
	public static final Compound.Class nontermRule = new Compound.Class(
		generateClass("NontermRule", GeneratedClass.Type.CLASS),
		"nonterm",
		new Compound.Item(null, new TerminalClass(token, LANGLE)),
		new Compound.Item(null, whitespaceRule),
		new Compound.Item("name", nontermNameRule),
		// TODO: subclass
		new Compound.Item(null, whitespaceRule),
		new Compound.Item(null, new TerminalClass(token, RANGLE)),
		new Compound.Item(null, whitespaceRule),
		new Compound.Item("type", new TerminalClass(token, RULE_DEF, REPEATING_RULE_DEF)),
		new Compound.Item("items", new Repeated(nontermItemRule.nominal, 0, null))
	);
	public static final Compound.Class extraCodeRule = new Compound.Class(
		generateClass("ExtraCodeRule", GeneratedClass.Type.CLASS),
		"extraCode",
		new Compound.Item("path", javaPathRule),
		new Compound.Item(null, new Repeated(blankLineRule, 1, null)),
		new Compound.Item(null, whitespaceRule),
		new Compound.Item(null, new TerminalClass(token, EXTRA_CODE_SEP)),
		new Compound.Item(null, blankLineRule),
		new Compound.Item("lines", new Repeated(new Compound(
			new TypeRef.List(token),
			after -> (ctx, indent) -> {
				ctx.output.append(indent);
				new TypeRef.List(token).generate(ctx.output);
				ctx.output.append(" tokens = tokens_.isEmpty() ? new ArrayList<>() : tokens_.get(0);\n");
				ctx.output.append(indent);
				ctx.output.append("tokens.add(newline);\n");
				ctx.output.append(indent);
				ctx.output.append("tokens.addAll(whitespace);\n");
				return after.withExpr("tokens", false).generate(ctx, indent);
			},
			new Compound.Item("tokens_", new Repeated(new Compound(
				new TypeRef.List(token),
				after -> (ctx, indent) -> {
					ctx.output.append(indent);
					ctx.output.append("tokens__.add(0, initial);\n");
					return after.withExpr("tokens__", false).generate(ctx, indent);
				},
				new Compound.Item("initial", new TerminalClass(token,
					Utils.setDifference(terminals.terminals.values(), Arrays.asList(NEWLINE, EXTRA_CODE_SEP)))),
				new Compound.Item("tokens__", new Repeated(
					new TerminalClass(token, Utils.setDifference(terminals.terminals.values(), Collections.singletonList(NEWLINE))),
					0, null
				))
			), 0, 1)),
			new Compound.Item("newline", new TerminalClass(token, NEWLINE)),
			new Compound.Item("whitespace", whitespaceRule)
		), 0, null)),
		new Compound.Item(null, new TerminalClass(token, EXTRA_CODE_SEP)),
		new Compound.Item(null, blankLineRule)
	);

	public static final Nominal itemRule;

	static {
		Compound.Class[] rules = new Compound.Class[]{
			terminalsRule,
			tokenRule,
			nontermRule,
			extraCodeRule
		};
		GeneratedClass cls = generateClass("ItemRule", GeneratedClass.Type.CLASS);
		cls.makeAbstract();
		Visitor visitor = new Visitor(cls);
		for(Compound.Class rule : rules) {
			rule.generatedClass.setSuperclass(cls.classRef);
			visitor.addSubclass(rule.generatedClass);
		}
		Element[] elements = new Element[rules.length];
		for(int i = 0; i < rules.length; i++) {
			elements[i] = rules[i].nominal;
		}
		itemRule = new Nominal(cls, new Alternative(cls.classRef.typeRef(), elements));
	}

	private DefinitionLanguage() {
	}
}
