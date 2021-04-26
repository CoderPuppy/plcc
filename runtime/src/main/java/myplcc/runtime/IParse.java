package myplcc.runtime;

@FunctionalInterface
public interface IParse<T extends ITerminal, R> {
	R parse(IParseState<T> parse) throws ParseException;
}
