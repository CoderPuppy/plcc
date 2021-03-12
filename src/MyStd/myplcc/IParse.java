package myplcc;

@FunctionalInterface
public interface IParse<T extends ITerminal, R> {
	R parse(Scan<T> scan, ITrace<T> trace);
}
