package myplcc.lexer;

import myplcc.TypeRef;

public interface Token extends TypeRef {
	Terminals getTerminals();
}
