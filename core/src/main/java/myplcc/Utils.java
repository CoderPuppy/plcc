package myplcc;

import myplcc.lexer.Terminal;
import myplcc.lexer.Terminals;

import java.util.*;
import java.util.function.BiFunction;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

public final class Utils {
	private Utils() {
	}

	public static final Pattern SPECIAL_CHAR_PAT = Pattern.compile("[\\\\\"[^\\p{Print}]]");

	public static String escapeString(String s) {
		StringBuilder output = new StringBuilder();
		output.append('"');
		Matcher matcher = SPECIAL_CHAR_PAT.matcher(s);
		int lastEnd = 0;
		while(matcher.find()) {
			if(lastEnd < matcher.start())
				output.append(s, lastEnd, matcher.start());
			for(char c : matcher.group().toCharArray()) {
				output.append("\\u");
				String hex = Integer.toString(c, 16);
				for(int i = 0; i < 5 - hex.length(); i++) {
					output.append('0');
				}
				output.append(hex);
			}
			lastEnd = matcher.end() + 1;
		}
		if(lastEnd < s.length())
			output.append(s, lastEnd, s.length());
		output.append('"');
		return output.toString();
	}

	public static <T> Set<T> setDifference(Collection<T> pos, Collection<T> neg) {
		Set<T> diff = new HashSet<>(pos);
		diff.removeAll(neg);
		return diff;
	}

	public static Generator.Method generateBinarySwitch(Set<Terminal> _setA, Generator.Method _genA, Generator.Method _genB) {
		return (ctx, indent) -> {
			Terminals terminals = null;
			Set<Terminal> setA = _setA;
			Generator.Method genA = _genA;
			Generator.Method genB = _genB;

			if(!setA.isEmpty()) {
				terminals = setA.iterator().next().terminals;
				Set<Terminal> setB = new HashSet<>(terminals.terminals.values());
				setB.removeAll(setA);

				if(setB.size() < setA.size()) {
					setA = setB;

					Generator.Method tmpGen = genA;
					genA = genB;
					genB = tmpGen;
				}
			}

			if(setA.isEmpty()) {
				if(genB == null)
					return true;
				else
					return genB.generate(ctx, indent);
			} else if(setA.size() == 1) {
				// this whole thing is only probably safe
				// the terminals class should be imported (in order to have scan$)
				// terminals should not be null here (otherwise setA would be empty)
				// it's also not necessary, just generates slightly cleaner code

				boolean returns = false;

				char eq = '=';
				if(genA == null) {
					if(genB == null)
						return true;
					genA = genB;
					genB = null;
					eq = '!';
				}

				ctx.output.append(indent);
				ctx.output.append("if(scan$.getCurrentToken().terminal ");
				ctx.output.append(eq);
				ctx.output.append("= ");
				terminals.generatedClass.classRef.generateCls(ctx.output);
				ctx.output.append('.');
				ctx.output.append(setA.iterator().next().name);
				ctx.output.append(") {\n");
				if(genA.generate(ctx, indent + "\t"))
					returns = true;

				if(genB != null) {
					ctx.output.append(indent);
					ctx.output.append("} else {\n");
					if(genB.generate(ctx, indent + "\t"))
						returns = true;
				}

				ctx.output.append(indent);
				ctx.output.append("}\n");

				return returns;
			} else {
				boolean returns = false;

				ctx.output.append(indent);
				ctx.output.append("switch(scan$.getCurrentToken().terminal) {\n");

				for(Terminal t : setA) {
					ctx.output.append(indent);
					ctx.output.append("\tcase ");
					ctx.output.append(t.name);
					ctx.output.append(":\n");
				}
				if(genA == null || genA.generate(ctx, indent + "\t\t")) {
					returns = true;
					ctx.output.append(indent);
					ctx.output.append("\t\tbreak;\n");
				}

				ctx.output.append(indent);
				ctx.output.append("\tdefault:\n");
				if(genB == null || genB.generate(ctx, indent + "\t\t"))
					returns = true;

				ctx.output.append(indent);
				ctx.output.append("}\n");

				return returns;
			}
		};
	}

	public static <A, B, C> Stream<C> zip(
		Stream<? extends A> a,
		Stream<? extends B> b,
		BiFunction<? super A, ? super B, ? extends C> zipper
	) {
		Objects.requireNonNull(zipper);
		Spliterator<? extends A> aSpliterator = Objects.requireNonNull(a).spliterator();
		Spliterator<? extends B> bSpliterator = Objects.requireNonNull(b).spliterator();

		// Zipping loses DISTINCT and SORTED characteristics
		int characteristics = aSpliterator.characteristics() & bSpliterator.characteristics() &
			~(Spliterator.DISTINCT | Spliterator.SORTED);

		long zipSize = ((characteristics & Spliterator.SIZED) != 0)
			? Math.min(aSpliterator.getExactSizeIfKnown(), bSpliterator.getExactSizeIfKnown())
			: -1;

		Iterator<A> aIterator = Spliterators.iterator(aSpliterator);
		Iterator<B> bIterator = Spliterators.iterator(bSpliterator);
		Iterator<C> cIterator = new Iterator<C>() {
			@Override
			public boolean hasNext() {
				return aIterator.hasNext() && bIterator.hasNext();
			}

			@Override
			public C next() {
				return zipper.apply(aIterator.next(), bIterator.next());
			}
		};

		Spliterator<C> split = Spliterators.spliterator(cIterator, zipSize, characteristics);
		return (a.isParallel() || b.isParallel())
			? StreamSupport.stream(split, true)
			: StreamSupport.stream(split, false);
	}
}
