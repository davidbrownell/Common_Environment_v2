# Generated from C:\Temp\QueryParser\Grammars\BuildEnvironment\..\QueryParser.g4 by ANTLR 4.6
# encoding: utf-8
from __future__ import print_function
from antlr4 import *
from io import StringIO

def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\3")
        buf.write(u"\31(\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\3\2\7\2\f\n\2\f")
        buf.write(u"\2\16\2\17\13\2\3\3\3\3\3\3\5\3\24\n\3\3\4\3\4\3\4\3")
        buf.write(u"\4\3\4\3\4\3\4\5\4\35\n\4\3\5\3\5\3\5\3\5\3\5\5\5$\n")
        buf.write(u"\5\5\5&\n\5\3\5\2\2\6\2\4\6\b\2\6\3\2\b\t\3\2\n\21\4")
        buf.write(u"\2\25\26\30\31\3\2\3\4)\2\r\3\2\2\2\4\20\3\2\2\2\6\34")
        buf.write(u"\3\2\2\2\b%\3\2\2\2\n\f\5\4\3\2\13\n\3\2\2\2\f\17\3\2")
        buf.write(u"\2\2\r\13\3\2\2\2\r\16\3\2\2\2\16\3\3\2\2\2\17\r\3\2")
        buf.write(u"\2\2\20\23\5\6\4\2\21\22\t\2\2\2\22\24\5\4\3\2\23\21")
        buf.write(u"\3\2\2\2\23\24\3\2\2\2\24\5\3\2\2\2\25\26\7\24\2\2\26")
        buf.write(u"\27\t\3\2\2\27\35\5\b\5\2\30\31\7\6\2\2\31\32\5\4\3\2")
        buf.write(u"\32\33\7\7\2\2\33\35\3\2\2\2\34\25\3\2\2\2\34\30\3\2")
        buf.write(u"\2\2\35\7\3\2\2\2\36&\7\22\2\2\37&\7\23\2\2 #\t\4\2\2")
        buf.write(u"!\"\t\5\2\2\"$\7\27\2\2#!\3\2\2\2#$\3\2\2\2$&\3\2\2\2")
        buf.write(u"%\36\3\2\2\2%\37\3\2\2\2% \3\2\2\2&\t\3\2\2\2\7\r\23")
        buf.write(u"\34#%")
        return buf.getvalue()


class QueryParserParser ( Parser ):

    grammarFileName = "QueryParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ u"<INVALID>", u"'+'", u"'-'", u"<INVALID>", u"'('", 
                     u"')'", u"'and'", u"'or'", u"'=='", u"'!='", u"'<'", 
                     u"'<='", u"'>'", u"'>='", u"'~'", u"'under'", u"<INVALID>", 
                     u"<INVALID>", u"<INVALID>", u"'@today'", u"'@now'" ]

    symbolicNames = [ u"<INVALID>", u"<INVALID>", u"<INVALID>", u"WS", u"LPAREN", 
                      u"RPAREN", u"AND", u"OR", u"EQUAL", u"NOT_EQUAL", 
                      u"LT", u"LTE", u"GT", u"GTE", u"LIKE", u"UNDER", u"NUMBER", 
                      u"INT", u"ID", u"TODAY", u"NOW", u"TIME_DELTA", u"DOUBLE_QUOTE_STRING", 
                      u"SINGLE_QUOTE_STRING" ]

    RULE_statements = 0
    RULE_expression = 1
    RULE_atom = 2
    RULE_value = 3

    ruleNames =  [ u"statements", u"expression", u"atom", u"value" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    WS=3
    LPAREN=4
    RPAREN=5
    AND=6
    OR=7
    EQUAL=8
    NOT_EQUAL=9
    LT=10
    LTE=11
    GT=12
    GTE=13
    LIKE=14
    UNDER=15
    NUMBER=16
    INT=17
    ID=18
    TODAY=19
    NOW=20
    TIME_DELTA=21
    DOUBLE_QUOTE_STRING=22
    SINGLE_QUOTE_STRING=23

    def __init__(self, input):
        super(QueryParserParser, self).__init__(input)
        self.checkVersion("4.6")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None



    class StatementsContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(QueryParserParser.StatementsContext, self).__init__(parent, invokingState)
            self.parser = parser

        def expression(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(QueryParserParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(QueryParserParser.ExpressionContext,i)


        def getRuleIndex(self):
            return QueryParserParser.RULE_statements

        def accept(self, visitor):
            if hasattr(visitor, "visitStatements"):
                return visitor.visitStatements(self)
            else:
                return visitor.visitChildren(self)




    def statements(self):

        localctx = QueryParserParser.StatementsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_statements)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 11
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==QueryParserParser.LPAREN or _la==QueryParserParser.ID:
                self.state = 8
                self.expression()
                self.state = 13
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class ExpressionContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(QueryParserParser.ExpressionContext, self).__init__(parent, invokingState)
            self.parser = parser

        def atom(self):
            return self.getTypedRuleContext(QueryParserParser.AtomContext,0)


        def expression(self):
            return self.getTypedRuleContext(QueryParserParser.ExpressionContext,0)


        def AND(self):
            return self.getToken(QueryParserParser.AND, 0)

        def OR(self):
            return self.getToken(QueryParserParser.OR, 0)

        def getRuleIndex(self):
            return QueryParserParser.RULE_expression

        def accept(self, visitor):
            if hasattr(visitor, "visitExpression"):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = QueryParserParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_expression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 14
            self.atom()
            self.state = 17
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==QueryParserParser.AND or _la==QueryParserParser.OR:
                self.state = 15
                _la = self._input.LA(1)
                if not(_la==QueryParserParser.AND or _la==QueryParserParser.OR):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 16
                self.expression()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class AtomContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(QueryParserParser.AtomContext, self).__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(QueryParserParser.ID, 0)

        def value(self):
            return self.getTypedRuleContext(QueryParserParser.ValueContext,0)


        def LPAREN(self):
            return self.getToken(QueryParserParser.LPAREN, 0)

        def expression(self):
            return self.getTypedRuleContext(QueryParserParser.ExpressionContext,0)


        def RPAREN(self):
            return self.getToken(QueryParserParser.RPAREN, 0)

        def EQUAL(self):
            return self.getToken(QueryParserParser.EQUAL, 0)

        def NOT_EQUAL(self):
            return self.getToken(QueryParserParser.NOT_EQUAL, 0)

        def LT(self):
            return self.getToken(QueryParserParser.LT, 0)

        def LTE(self):
            return self.getToken(QueryParserParser.LTE, 0)

        def GT(self):
            return self.getToken(QueryParserParser.GT, 0)

        def GTE(self):
            return self.getToken(QueryParserParser.GTE, 0)

        def LIKE(self):
            return self.getToken(QueryParserParser.LIKE, 0)

        def UNDER(self):
            return self.getToken(QueryParserParser.UNDER, 0)

        def getRuleIndex(self):
            return QueryParserParser.RULE_atom

        def accept(self, visitor):
            if hasattr(visitor, "visitAtom"):
                return visitor.visitAtom(self)
            else:
                return visitor.visitChildren(self)




    def atom(self):

        localctx = QueryParserParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_atom)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 26
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [QueryParserParser.ID]:
                self.state = 19
                self.match(QueryParserParser.ID)
                self.state = 20
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << QueryParserParser.EQUAL) | (1 << QueryParserParser.NOT_EQUAL) | (1 << QueryParserParser.LT) | (1 << QueryParserParser.LTE) | (1 << QueryParserParser.GT) | (1 << QueryParserParser.GTE) | (1 << QueryParserParser.LIKE) | (1 << QueryParserParser.UNDER))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 21
                self.value()
                pass
            elif token in [QueryParserParser.LPAREN]:
                self.state = 22
                self.match(QueryParserParser.LPAREN)
                self.state = 23
                self.expression()
                self.state = 24
                self.match(QueryParserParser.RPAREN)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class ValueContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(QueryParserParser.ValueContext, self).__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(QueryParserParser.NUMBER, 0)

        def INT(self):
            return self.getToken(QueryParserParser.INT, 0)

        def DOUBLE_QUOTE_STRING(self):
            return self.getToken(QueryParserParser.DOUBLE_QUOTE_STRING, 0)

        def SINGLE_QUOTE_STRING(self):
            return self.getToken(QueryParserParser.SINGLE_QUOTE_STRING, 0)

        def TODAY(self):
            return self.getToken(QueryParserParser.TODAY, 0)

        def NOW(self):
            return self.getToken(QueryParserParser.NOW, 0)

        def TIME_DELTA(self):
            return self.getToken(QueryParserParser.TIME_DELTA, 0)

        def getRuleIndex(self):
            return QueryParserParser.RULE_value

        def accept(self, visitor):
            if hasattr(visitor, "visitValue"):
                return visitor.visitValue(self)
            else:
                return visitor.visitChildren(self)




    def value(self):

        localctx = QueryParserParser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_value)
        self._la = 0 # Token type
        try:
            self.state = 35
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [QueryParserParser.NUMBER]:
                self.enterOuterAlt(localctx, 1)
                self.state = 28
                self.match(QueryParserParser.NUMBER)
                pass
            elif token in [QueryParserParser.INT]:
                self.enterOuterAlt(localctx, 2)
                self.state = 29
                self.match(QueryParserParser.INT)
                pass
            elif token in [QueryParserParser.TODAY, QueryParserParser.NOW, QueryParserParser.DOUBLE_QUOTE_STRING, QueryParserParser.SINGLE_QUOTE_STRING]:
                self.enterOuterAlt(localctx, 3)
                self.state = 30
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << QueryParserParser.TODAY) | (1 << QueryParserParser.NOW) | (1 << QueryParserParser.DOUBLE_QUOTE_STRING) | (1 << QueryParserParser.SINGLE_QUOTE_STRING))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 33
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==QueryParserParser.T__0 or _la==QueryParserParser.T__1:
                    self.state = 31
                    _la = self._input.LA(1)
                    if not(_la==QueryParserParser.T__0 or _la==QueryParserParser.T__1):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()
                    self.state = 32
                    self.match(QueryParserParser.TIME_DELTA)


                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





