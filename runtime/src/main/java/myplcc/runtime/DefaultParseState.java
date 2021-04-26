package myplcc.runtime;

import java.util.ArrayList;
import java.util.List;

public class DefaultParseState<T extends ITerminal> implements IParseState<T> {
	public final Scan<T> scan;
	public final List<ITrace<T>> traceStack = new ArrayList<>();
	public final List<String> contextStack = new ArrayList<>();

	public DefaultParseState(Scan<T> scan) {
		this(scan, null);
	}

	public DefaultParseState(Scan<T> scan, ITrace<T> trace) {
		this.scan = scan;
		traceStack.add(trace);
	}

	public ITrace<T> getTrace() {
		if(traceStack.isEmpty())
			return null;
		return traceStack.get(traceStack.size() - 1);
	}

	@Override
	public T getCurrentTerminal() {
		return scan.getCurrentToken().terminal;
	}

	@Override
	public Token<T> take() {
		return scan.take(getTrace());
	}

	@Override
	public void enter(String ctx) {
		contextStack.add(ctx);
		ITrace<T> trace = getTrace();
		if(trace != null)
			traceStack.add(trace.nonterm(ctx, scan.getLineNumber()));
	}

	@Override
	public void leave() {
		contextStack.remove(contextStack.size() - 1);
		if(!traceStack.isEmpty())
			traceStack.remove(traceStack.size() - 1);
	}
}
