package myplcc.grammar;

import myplcc.*;
import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.io.IOException;
import java.util.*;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.stream.Collectors;

public class Compound implements Element {
	public final TypeRef outputType;
	public final Function<Generator.ExprSink, Generator.Method> result;
	public final List<Item> items;
	private Set<Terminal> firstSet = null;
	private boolean possiblyEmpty = true;
	public final boolean hasSeparator;

	public Compound(TypeRef outputType, Function<Generator.ExprSink, Generator.Method> result, Item... items) {
		this(outputType, result, Arrays.asList(items));
	}

	public Compound(TypeRef outputType, Function<Generator.ExprSink, Generator.Method> result, List<Item> items) {
		this.outputType = outputType;
		this.result = result;
		this.items = items;
		this.hasSeparator = items.stream().anyMatch(item -> item.element.hasSeparator());
	}

	@Override
	public Generator.Method generateParse(Generator.ExprSink after, String explicitRepCtx) {
		return (ctx, indent) -> {
			for(Item item : items) {
				if(item.field != null) {
					ctx.output.append(indent);
					item.element.getOutputType().generate(ctx.output);
					ctx.output.append(' ');
					ctx.output.append(item.field);
					ctx.output.append(";\n");
				}
				item.element.generateParse((expr, required) -> (ctx1, indent1) -> {
					if(item.field != null || required) {
						ctx1.output.append(indent1);
						if(item.field != null) {
							ctx1.output.append(item.field);
							ctx1.output.append(" = ");
						}
						ctx1.output.append(expr);
						ctx1.output.append(";\n");
					}
					return true;
				}, explicitRepCtx).generate(ctx, indent);
			}

			return result.apply(after).generate(ctx, indent);
		};
	}

	private void compute(boolean initial) {
		if(initial && firstSet != null)
			return;
		Set<Terminal> firstSet = new HashSet<>();
		for(Item item : items) {
			Set<Terminal> conflict = new HashSet<>(firstSet);
			conflict.retainAll(item.element.getFirstSet());
			if(!conflict.isEmpty())
				throw new RuntimeException("TODO: conflict");

			firstSet.addAll(item.element.getFirstSet());

			if(!item.element.isPossiblyEmpty()) {
				if(initial) {
					this.firstSet = firstSet;
					this.possiblyEmpty = false;
					return;
				} else {
					firstSet = new HashSet<>();
				}
			}
		}
		if(initial) {
			this.firstSet = firstSet;
			this.possiblyEmpty = true;
		}
	}

	@Override
	public Set<Terminal> getFirstSet() {
		compute(true);
		return firstSet;
	}

	@Override
	public boolean isPossiblyEmpty() {
		compute(true);
		return possiblyEmpty;
	}

	@Override
	public void checkLL1() {
		compute(false);
		for(Item item : items) {
			item.element.checkLL1();
		}
	}

	@Override
	public boolean hasSeparator() {
		return hasSeparator;
	}

	@Override
	public TypeRef getOutputType() {
		return outputType;
	}

	@Override
	public Terminals getTerminals() {
		return items.iterator().next().element.getTerminals();
	}

	@Override
	public void addImports(Consumer<ClassRef> doImport) {
		Element.super.addImports(doImport);
		for(Item item : items) {
			item.element.addImports(doImport);
		}
	}

	public static class Item {
		public final String field;
		public final Element element;

		public Item(String field, Element element) {
			this.field = field;
			this.element = element;
		}
	}

	public static class Class {
		public final GeneratedClass generatedClass;
		public final Nominal nominal;
		public final DataClass dataClass;
		public final Compound compound;

		public Class(GeneratedClass generatedClass, String context, Item... items) {
			this(generatedClass, context, Arrays.asList(items));
		}

		public Class(GeneratedClass generatedClass, String context, List<Item> items) {
			this.generatedClass = generatedClass;
			dataClass = new DataClass(generatedClass,
				items.stream()
					.filter(item -> item.field != null)
					.collect(Collectors.toMap(
						item -> item.field,
						item -> item.element.getOutputType(),
						(var0, var1) -> {
							throw new IllegalStateException(String.format("Duplicate key %s", var0));
						},
						LinkedHashMap::new
					))
			);
			StringBuilder outExpr = new StringBuilder();
			outExpr.append("new ");
			try {
				generatedClass.classRef.generateCls(outExpr);
			} catch(IOException e) {
				// this should never happen because StringBuilder doesn't throw IOExceptions
				throw new RuntimeException(e);
			}
			outExpr.append("(");
			boolean sep = false;
			for(Item item : items) {
				if(item.field == null)
					continue;
				if(sep)
					outExpr.append(", ");
				sep = true;
				outExpr.append(item.field);
			}
			outExpr.append(")");
			String expr = outExpr.toString();
			compound = new Compound(
				generatedClass.classRef.typeRef(),
				after -> after.withExpr(expr, false),
				items
			);
			nominal = new Nominal(generatedClass, context == null ? compound : new Context(context, compound));
		}
	}
}
