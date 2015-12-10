grammar Selector;

tokens { INDENT, DEDENT }

@lexer::header {

from CommonEnvironment.Antlr4Helpers.DenterHelper import DenterHelper
from SimpleSchemaParser import SimpleSchemaParser

}

@lexer::members {

multiline_statement_ctr = 0

def nextToken(self):
    if not hasattr(self, "_denter"):
        self._denter = DenterHelper( super(SimpleSchemaLexer, self).nextToken,
                                     SimpleSchemaParser.NEWLINE,
                                     SimpleSchemaParser.INDENT,
                                     SimpleSchemaParser.DEDENT,
                                   )

    return self._denter.nextToken()

}

// ---------------------------------------------------------------------------
// |
// |  Lexer Rules
// |
// ---------------------------------------------------------------------------
MULTI_LINE_NEWLINE:                         { SimpleSchemaLexer.multiline_statement_ctr != 0 }? '\r'? '\n' -> skip;
NEWLINE:                                    { SimpleSchemaLexer.multiline_statement_ctr == 0 }? '\r'? '\n' [ \t]*;
MULTI_LINE_ESCAPE:                          '\\' '\r'? '\n' -> skip;
HORIZONTAL_WHITESPACE:                      [ \t]+ -> skip;

COMMENT:                                    '#' ~[\r\n]* -> skip;

DECORATOR:                                  '::';
SCOPE_DELIMITER:                            ':';
SEP:                                        '/';
ANY:                                        '*';
LBRACK:                                     '[';
RBRACK:                                     ']';
LPAREN:                                     '(';
RPAREN:                                     ')';

INT:                                        '-'? [0-9]+;
NUMBER:                                     '-'? [0-9]* '.' [0-9]+;
ID:                                         '@'? [a-zA-Z_][a-zA-Z_0-9\-.]*;
DOUBLE_QUOTE_STRING:                        '"' (('\\"' | '\\\\') | .)*? '"';
SINGLE_QUOTE_STRING:                        '\'' (('\\\'' | '\\\\') | .)*? '\'';

// Keywords
PASS:                                       'pass';
DECORATOR_ANCESTORS:                        'ancestors';
DECORATOR_ANCESTORS_AND_SELF:               'ancestors_and_self';
DECORATOR_ATTRIBUTES:                       'attributes';
DECORATOR_CHILDREN:                         'children';
DECORATOR_SELF_AND_CHILDREN:                'self_and_children';
DECORATOR_DESCENDANTS:                      'descendants';
DECORATOR_SELF_AND_DESCENDANTS:             'self_and_descendants';
DECORATOR_SIBLINGS:                         'siblings';
DECORATOR_SIBLINGS_AND_SELF:                'siblings_and_self';

// ---------------------------------------------------------------------------
// |
// |  Parser Rules
// |
// ---------------------------------------------------------------------------
arg:                                        ID | INT | NUMBER | DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING;

statements:                                 statement+ EOF;

statement:                                  (singleStatement | groupStatement) NEWLINE+;

singleStatement:                            selector decorator? function;
groupStatement:                             selector decorator? function? SCOPE_DELIMITER ( PASS |
                                                                                            singleStatement |
                                                                                            ( NEWLINE INDENT ( (PASS NEWLINE) |
                                                                                                                (NEWLINE* statement)+
                                                                                                             )
                                                                                              DEDENT
                                                                                            )
                                                                                          );
                                                                              
function:                                   LPAREN (DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING) RPAREN;

selector:                                   SEP? (ANY | ID) selector_Predicate? (SEP (ANY | ID) selector_Predicate?)* SEP?;
selector_Predicate:                         LBRACK ( selector_Predicate_Index |
                                                     selector_Predicate_IndexRange |
                                                     selector_Predicate_Statement
                                                   )
                                            RBRACK;
                                            
selector_Predicate_Index:                   INT;
selector_Predicate_IndexRange:              INT? SCOPE_DELIMITER INT?;
selector_Predicate_Statement:               ID selector_Predicate_Statement_Operator arg;
selector_Predicate_Statement_Operator:      '==' | '!=' | '<' | '<=' | '>' | '>=';

decorator:                                  DECORATOR ( DECORATOR_ANCESTORS |
                                                        DECORATOR_ANCESTORS_AND_SELF |
                                                        DECORATOR_ATTRIBUTES |
                                                        DECORATOR_CHILDREN |
                                                        DECORATOR_SELF_AND_CHILDREN |
                                                        DECORATOR_DESCENDANTS |
                                                        DECORATOR_SELF_AND_DESCENDANTS |
                                                        DECORATOR_SIBLINGS |
                                                        DECORATOR_SIBLINGS_AND_SELF
                                                      );
                                            