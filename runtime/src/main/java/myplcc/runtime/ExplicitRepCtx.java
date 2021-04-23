package myplcc.runtime;

public class ExplicitRepCtx {
	public boolean defined = false;
	public boolean more;

	public void define(boolean more) {
		assert !defined;
		defined = true;
		this.more = more;
	}
	public void reset() {
		defined = false;
	}
}
