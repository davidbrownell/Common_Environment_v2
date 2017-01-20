grammar QueryParser;

// ---------------------------------------------------------------------------
// |
// |  Lexer Rules
// |
// ---------------------------------------------------------------------------
WS:                                         [ \t] -> skip;

LPAREN:                                     '(';
RPAREN:                                     ')';

AND:                                        'and';
OR:                                         'or';

EQUAL:                                      '==';
NOT_EQUAL:                                  '!=';
LT:                                         '<';
LTE:                                        '<=';
GT:                                         '>';
GTE:                                        '>=';
LIKE:                                       '~';
UNDER:                                      'under';

NUMBER:                                     '-'? [0-9]* '.' [0-9]+;
INT:                                        '-'? [0-9]+;
ID:                                         [a-zA-Z_][a-zA-Z_0-9\-.]*;

TODAY:                                      '@today';
NOW:                                        '@now';
TIME_DELTA:                                 [0-9]+ ( 'Y' |  // Years
                                                     'W' |  // Weeks
                                                     'M' |  // Months
                                                     'D' |  // Days
                                                     'h' |  // hours
                                                     'm' |  // minutes
                                                     's' |  // seconds
                                                     'mi'   // microseconds
                                                   );
                                                    
DOUBLE_QUOTE_STRING:                        '"' ('\\"' | '\\\\' | .)*? '"';
SINGLE_QUOTE_STRING:                        '\'' ('\\\'' | '\\\\' | .)*? '\'';

// ---------------------------------------------------------------------------
// |
// |  Parser Rules
// |    Note that anything with a '__' suffix represents a non-binding rule
// |    (it does not have code explicitly associated with it).
// |
// ---------------------------------------------------------------------------
statements:                                 statement+;						// Entry point, not decorated

statement:									expression ((AND | OR) expression)*;

expression:                                 ( ID (EQUAL | NOT_EQUAL | LT | LTE | GT | GTE | LIKE | UNDER) value |
                                              LPAREN statement RPAREN
                                            );
                                            
value:                                      NUMBER | INT | (DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING | TODAY | NOW) (('+' | '-') TIME_DELTA)?;
