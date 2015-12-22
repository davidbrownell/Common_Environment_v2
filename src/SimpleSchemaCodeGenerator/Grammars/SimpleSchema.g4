grammar SimpleSchema;

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

LPAREN:                                     '(' { SimpleSchemaLexer.multiline_statement_ctr += 1 };
RPAREN:                                     ')' { SimpleSchemaLexer.multiline_statement_ctr -= 1 };
LBRACK:                                     '[' { SimpleSchemaLexer.multiline_statement_ctr += 1 };
RBRACK:                                     ']' { SimpleSchemaLexer.multiline_statement_ctr -= 1 };
LT:                                         '<' { SimpleSchemaLexer.multiline_statement_ctr += 1 };
GT:                                         '>' { SimpleSchemaLexer.multiline_statement_ctr -= 1 };
LBRACE:                                     '{';
RBRACE:                                     '}';

MULTI_LINE_COMMENT:                         '#/' .*? '/#' -> skip;
COMMENT:                                    '#' ~[\r\n]* -> skip;

// Keywords
PASS:                                       'pass';
INCLUDE:                                    'include';
CONFIG:                                     'config';

STRING_TYPE:                                'string';
ENUM_TYPE:                                  'enum';
INTEGER_TYPE:                               'integer';
NUMBER_TYPE:                                'number';
BOOLEAN_TYPE:                               'boolean';
GUID_TYPE:                                  'guid';
DATETIME_TYPE:                              'datetime';
DATE_TYPE:                                  'date';
TIME_TYPE:                                  'time';
DURATION_TYPE:                              'duration';
FILENAME_TYPE:                              'filename';
CUSTOM_TYPE:                                'custom';

STRING_METADATA_VALIDATION:                 'validation';
STRING_METADATA_MIN_LENGTH:                 'min_length';
STRING_METADATA_MAX_LENGTH:                 'max_length';
ENUM_METADATA_VALUES:                       'values';
ENUM_METADATA_FRIENDLY_VALUES:              'friendly_values';
METADATA_MIN:                               'min';
METADATA_MAX:                               'max';
INTEGER_METADATA_BYTES:                     'bytes';
FILENAME_METADATA_TYPE:                     'type';
FILENAME_METADATA_MUST_EXIST:               'must_exist';
CUSTOM_METADATA_T:                          't';

GENERIC_METADATA_DESCRIPTION:               'description';
GENERIC_METADATA_PLURAL:                    'plural';
GENERIC_METADATA_DEFAULT:                   'default';
GENERIC_METADATA_POLYMORPHIC:               'polymorphic';
GENERIC_METADATA_SUPPRESS_POLYMORPHIC:      'suppress_polymorphic';

SCOPE_DELIMITER:                            ':';
ASSIGNMENT:                                 '=';
COMMA:                                      ',';

INT:                                        '-'? [0-9]+;
NUMBER:                                     '-'? [0-9]* '.' [0-9]+;
ID:                                         [a-zA-Z_][a-zA-Z_0-9\-.]*;

ARITY_OPTIONAL:                             '?';
ARITY_ZERO_OR_MORE:                         '*';
ARITY_ONE_OR_MORE:                          '+';

fragment HWS:                               [ \t];

DOUBLE_QUOTE_NUMBER:                        '"' NUMBER_VALUES '"';
SINGLE_QUOTE_NUMBER:                        '\'' NUMBER_VALUES '\'';
fragment NUMBER_VALUES:                     HWS* NUMBER HWS*;

DOUBLE_QUOTE_INT:                           '"' INT_VALUES '"';
SINGLE_QUOTE_INT:                           '\'' INT_VALUES '\'';
fragment INT_VALUES:                        HWS* INT HWS*;

DOUBLE_QUOTE_BOOL:                          '"' BOOL_VALUES '"';
SINGLE_QUOTE_BOOL:                          '\'' BOOL_VALUES '\'';
fragment BOOL_VALUES:                       HWS* ('true' | 't' | 'yes' | 'y' | '1' | 'false' | 'f' | 'no' | 'n' | '0') HWS*;

DOUBLE_QUOTE_FILENAME_TYPE:                 '"' FILENAME_TYPE_VALUES '"';
SINGLE_QUOTE_FILENAME_TYPE:                 '\'' FILENAME_TYPE_VALUES '\'';
fragment FILENAME_TYPE_VALUES:              HWS* ('file' | 'directory' | 'either') HWS*;

DOUBLE_QUOTE_STRING:                        '"' (('\\"' | '\\\\') | .)*? '"';
SINGLE_QUOTE_STRING:                        '\'' (('\\\'' | '\\\\') | .)*? '\'';

TRIPLE_DOUBLE_QUOTE_STRING:                 '"""' .*? '"""';
TRIPLE_SINGLE_QUOTE_STRING:                 '\'\'\'' .*? '\'\'\'';

// ---------------------------------------------------------------------------
// |
// |  Parser Rules
// |    Note that anything with a '__' suffix represents a non-binding rule
// |    (it does not have code explicitly associated with it).
// |
// ---------------------------------------------------------------------------
numberString:                               DOUBLE_QUOTE_NUMBER | SINGLE_QUOTE_NUMBER;
intString:                                  DOUBLE_QUOTE_INT | SINGLE_QUOTE_INT;
boolString:                                 DOUBLE_QUOTE_BOOL | SINGLE_QUOTE_BOOL;
filenameTypeString:                         DOUBLE_QUOTE_FILENAME_TYPE | SINGLE_QUOTE_FILENAME_TYPE;

string:                                     DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING |
                                            DOUBLE_QUOTE_NUMBER | SINGLE_QUOTE_NUMBER |
                                            DOUBLE_QUOTE_INT | SINGLE_QUOTE_INT |
                                            DOUBLE_QUOTE_BOOL | SINGLE_QUOTE_BOOL;

enhancedString:                             string |
                                            TRIPLE_DOUBLE_QUOTE_STRING | TRIPLE_SINGLE_QUOTE_STRING;

arg:                                        ID | INT | NUMBER | enhancedString | listArg;
listArg:                                    LBRACK arg (COMMA arg)* COMMA? RBRACK;

// Entry point, not decorated
statements:                                 ( ((unnamedObj | unnamedDeclaration) NEWLINE*) | 
                                              headerStatement__* standardStatement__*
                                            )
                                            EOF;

headerStatement__:                          (includeStatement__ | configDeclaration) NEWLINE+;

standardStatement__:                        (obj | declaration | extension) NEWLINE+;

includeStatement__:                         INCLUDE LPAREN includeStatement_Name RPAREN;
includeStatement_Name:                      string;

configDeclaration:                          CONFIG LPAREN configDeclaration_Name RPAREN SCOPE_DELIMITER configDeclaration_Content__;
configDeclaration_Name:                     string;
configDeclaration_Content__:                ( PASS |
                                              ( NEWLINE INDENT ( (PASS NEWLINE) |
                                                                 (NEWLINE* metadata__* NEWLINE)+
                                                               ) DEDENT
                                              )
                                            );

unnamedObj:                                 ( (LPAREN obj_Declaration__ RPAREN) |
                                              (LT obj_Declaration__ GT)
                                            ) obj_Content__;

obj:                                        ( (LPAREN obj_Name obj_Base? obj_Declaration__ RPAREN) |
                                              (LT obj_Name obj_Base? obj_Declaration__ GT)
                                            ) obj_Content__;

obj_Name:                                   ID;
obj_Base:                                   declaration_Type;

obj_Declaration__:                          declaration_Metadata__* metadata__* arity__?;

obj_Content__:                              SCOPE_DELIMITER ( PASS |
                                                              declaration |
                                                              ( NEWLINE INDENT ( (PASS NEWLINE) |
                                                                                 (NEWLINE* standardStatement__)+
                                                                               )
                                                                        DEDENT
                                                              )
                                                            );

unnamedDeclaration:                         (LPAREN declaration_Content__ RPAREN) |
                                            (LBRACK declaration_Content__ RBRACK) |
                                            (LT declaration_Content__ GT);

declaration:                                (LPAREN declaration_Name declaration_Content__ RPAREN) |
                                            (LBRACK declaration_Name declaration_Content__ RBRACK) |
                                            (LT declaration_Name declaration_Content__ GT);

declaration_Name:                           ID;
declaration_Content__:                      declaration_Type declaration_Metadata__* metadata__* arity__?;

declaration_Type:                           (STRING_TYPE stringMetadata__*) |
                                            (ENUM_TYPE enumValues__ enumMetadata__*) |
                                            (INTEGER_TYPE integerMetadata__*) |
                                            (NUMBER_TYPE numberMetadata__*) |
                                            (FILENAME_TYPE filenameMetadata__*) |
                                            (CUSTOM_TYPE customValues__*) |
                                            BOOLEAN_TYPE |
                                            GUID_TYPE |
                                            DATETIME_TYPE |
                                            DATE_TYPE |
                                            TIME_TYPE |
                                            DURATION_TYPE |
                                            ID;

declaration_Metadata__:                     (declaration_Metadata_Description ASSIGNMENT string) |
                                            (declaration_Metadata_Plural ASSIGNMENT string) |
                                            (declaration_Metadata_Default ASSIGNMENT string) |
                                            (declaration_Metadata_Polymorphic ASSIGNMENT boolString) |
                                            (declaration_Metadata_SuppressPolymorphic ASSIGNMENT boolString);
                                            

declaration_Metadata_Description:           GENERIC_METADATA_DESCRIPTION;
declaration_Metadata_Plural:                GENERIC_METADATA_PLURAL;
declaration_Metadata_Default:               GENERIC_METADATA_DEFAULT;
declaration_Metadata_Polymorphic:           GENERIC_METADATA_POLYMORPHIC;
declaration_Metadata_SuppressPolymorphic:   GENERIC_METADATA_SUPPRESS_POLYMORPHIC;

stringMetadata__:                           (stringMetadata_Validation ASSIGNMENT string) |
                                            (stringMetadata_MaxLength ASSIGNMENT intString) |
                                            (stringMetadata_MinLength ASSIGNMENT intString);

stringMetadata_Validation:                  STRING_METADATA_VALIDATION;
stringMetadata_MaxLength:                   STRING_METADATA_MAX_LENGTH;
stringMetadata_MinLength:                   STRING_METADATA_MIN_LENGTH;

enumValues__:                               enumValues_Values ASSIGNMENT enum_StringList;
enumValues_Values:                          ENUM_METADATA_VALUES;
enumMetadata__:                             enumMetadata_FriendlyValues ASSIGNMENT enum_StringList;
enumMetadata_FriendlyValues:                ENUM_METADATA_FRIENDLY_VALUES;
enum_StringList:                            LBRACK string (COMMA string)* COMMA? RBRACK;

integerMetadata__:                          (integerMetadata_Bytes ASSIGNMENT intString) |
                                            (integerMetadata_Max ASSIGNMENT intString) |
                                            (integerMetadata_Min ASSIGNMENT intString);

integerMetadata_Bytes:                      INTEGER_METADATA_BYTES;
integerMetadata_Max:                        METADATA_MAX;
integerMetadata_Min:                        METADATA_MIN;
                                            
numberMetadata__:                           (numberMetadata_Max ASSIGNMENT numberString) |
                                            (numberMetadata_Min ASSIGNMENT numberString);

numberMetadata_Max:                         METADATA_MAX;
numberMetadata_Min:                         METADATA_MIN;

filenameMetadata__:                         (filenameMetadata_Type ASSIGNMENT filenameTypeString) |
                                            (filenameMetadata_MustExist ASSIGNMENT boolString);

filenameMetadata_Type:                      FILENAME_METADATA_TYPE;
filenameMetadata_MustExist:                 FILENAME_METADATA_MUST_EXIST;

customValues__:                             customValues_Type ASSIGNMENT string;
customValues_Type:                          CUSTOM_METADATA_T;

metadata__:                                 metadata_Name ASSIGNMENT string;
metadata_Name:                              ID;

arity__:                                    arity_Optional | arity_ZeroOrMore | arity_OneOrMore | arity_Custom | arity_CustomRange;
arity_Optional:                             ARITY_OPTIONAL;
arity_ZeroOrMore:                           ARITY_ZERO_OR_MORE;
arity_OneOrMore:                            ARITY_ONE_OR_MORE;
arity_Custom:                               LBRACE INT RBRACE;
arity_CustomRange:                          LBRACE INT COMMA INT RBRACE;

extension:                                  extension_Name ( (LPAREN RPAREN) |
                                                             (LPAREN extension_Content__ RPAREN)
                                                           ) arity__?;

extension_Name:                             ID;

extension_Content__:                        extension_Content_Standard__ | extension_Content_Keywords__;
extension_Content_Standard__:               extension_Content_Positional (COMMA extension_Content_Positional)* (COMMA extension_Content_Keywords__)?;
extension_Content_Positional:               arg;
extension_Content_Keywords__:               extension_Content_Keyword__ (COMMA extension_Content_Keyword__)* COMMA?;
extension_Content_Keyword__:                extension_Content_Keyword_Name ASSIGNMENT arg;
extension_Content_Keyword_Name:             ID;
