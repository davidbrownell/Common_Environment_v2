grammar Selector;

tokens { INDENT, DEDENT }

@lexer::header {

from CommonEnvironment.Antlr4Helpers.DenterHelper import DenterHelper
from SelectorParser import SelectorParser

}

@lexer::members {

multiline_statement_ctr = 0

def nextToken(self):
    if not hasattr(self, "_denter"):
        self._denter = DenterHelper( super(SelectorLexer, self).nextToken,
                                     SelectorParser.NEWLINE,
                                     SelectorParser.INDENT,
                                     SelectorParser.DEDENT,
                                   )

    return self._denter.nextToken()

}

// ---------------------------------------------------------------------------
// |
// |  Lexer Rules
// |
// ---------------------------------------------------------------------------
MULTI_LINE_NEWLINE:                         { SelectorLexer.multiline_statement_ctr != 0 }? '\r'? '\n' -> skip;
NEWLINE:                                    { SelectorLexer.multiline_statement_ctr == 0 }? '\r'? '\n' [ \t]*;
MULTI_LINE_ESCAPE:                          '\\' '\r'? '\n' -> skip;
HORIZONTAL_WHITESPACE:                      [ \t]+ -> skip;

MULTI_LINE_COMMENT:                         '#/' .*? '/#' -> skip;
COMMENT:                                    '#' ~[\r\n]* -> skip;

SCOPE_DELIMITER:                            ':';
SEP:                                        '/';
ONE_OR_MORE:                                '+';
ZERO_OR_MORE:                               '*';
ANY:                                        '.';
LT:                                         '<';
GT:                                         '>';
LBRACK:                                     '[';
RBRACK:                                     ']';
LPAREN:                                     '(';
RPAREN:                                     ')';
LBRACE:                                     '{';
RBRACE:                                     '}';
COMMA:                                      ',';

INT:                                        '-'? [0-9]+;
ID:                                         [a-zA-Z_][a-zA-Z_0-9\-.]*;

// Keywords
PASS:                                       'pass';

PREDICATE_OBJECT:                           'object';
PREDICATE_SIMPLE_OBJECT:                    'simple';
PREDICATE_COMPOUND_OBJECT:                  'compound';
PREDICATE_FUNDAMENTAL:                      'fundamental';

PREDICATE_STRING:                           'string';
PREDICATE_ENUM:                             'enum';
PREDICATE_INTEGER:                          'integer';
PREDICATE_NUMBER:                           'number';
PREDICATE_BOOLEAN:                          'boolean';
PREDICATE_GUID:                             'guid';
PREDICATE_DATETIME:                         'datetime';
PREDICATE_DATE:                             'date';
PREDICATE_TIME:                             'time';
PREDICATE_DURATION:                         'duration';
PREDICATE_FILENAME:                         'filename';
PREDICATE_CUSTOM:                           'custom';

CALL_TYPE_PRE:                              'pre';
CALL_TYPE_POST:                             'post';
CALL_TYPE_INLINE:                           'inline';

DECORATOR_SELF:                             'self';
DECORATOR_ANCESTORS:                        'ancestors';
DECORATOR_ANCESTORS_AND_SELF:               'ancestors_and_self';
DECORATOR_CHILDREN:                         'children';
DECORATOR_SELF_AND_CHILDREN:                'self_and_children';
DECORATOR_DESCENDANTS:                      'descendants';
DECORATOR_SELF_AND_DESCENDANTS:             'self_and_descendants';
DECORATOR_SIBLINGS:                         'siblings';
DECORATOR_SELF_AND_SIBLINGS:                'self_and_siblings';

// ---------------------------------------------------------------------------
// |
// |  Parser Rules
// |
// ---------------------------------------------------------------------------
statements:                                 statement___+ EOF;

statement___:                               (single_statement | compound_statement) NEWLINE+;

single_statement:                           selector ID call_type___? decorator?;
compound_statement:                         selector (ID call_type___? decorator?)? SCOPE_DELIMITER ( PASS |
                                                                                                      single_statement |
                                                                                                      ( NEWLINE INDENT( (PASS NEWLINE) |
                                                                                                                        (NEWLINE* statement___)+
                                                                                                                      )
                                                                                                        DEDENT
                                                                                                      )
                                                                                                    );

selector:                                   SEP? selector_item selector_predicate? (SEP selector_item selector_predicate?)* SEP?;

selector_item:                              ( ANY (LBRACE (INT | INT COMMA INT) RBRACE)? |
                                              ONE_OR_MORE |
                                              ZERO_OR_MORE |
                                              ID
                                            );

selector_predicate:                         LBRACK ( PREDICATE_OBJECT |
                                                     PREDICATE_SIMPLE_OBJECT |
                                                     PREDICATE_COMPOUND_OBJECT |
                                                     PREDICATE_FUNDAMENTAL |
                                                     PREDICATE_STRING |
                                                     PREDICATE_ENUM |
                                                     PREDICATE_INTEGER |
                                                     PREDICATE_NUMBER |
                                                     PREDICATE_BOOLEAN |
                                                     PREDICATE_GUID |
                                                     PREDICATE_DATETIME |
                                                     PREDICATE_DATE |
                                                     PREDICATE_TIME |
                                                     PREDICATE_DURATION |
                                                     PREDICATE_FILENAME |
                                                     PREDICATE_CUSTOM
                                                   )
                                            RBRACK;
                                            
call_type___:                               LT call_type_type (COMMA call_type_type)* COMMA? GT;
call_type_type:                             CALL_TYPE_PRE | CALL_TYPE_POST | CALL_TYPE_INLINE;

decorator:                                  LPAREN ( DECORATOR_SELF |
                                                     DECORATOR_ANCESTORS |
                                                     DECORATOR_ANCESTORS_AND_SELF |
                                                     DECORATOR_CHILDREN |
                                                     DECORATOR_SELF_AND_CHILDREN |
                                                     DECORATOR_DESCENDANTS |
                                                     DECORATOR_SELF_AND_DESCENDANTS |
                                                     DECORATOR_SIBLINGS |
                                                     DECORATOR_SELF_AND_SIBLINGS
                                                   )
                                            RPAREN;
