# Generated from C:\Temp\QueryParser\Grammars\BuildEnvironment\..\QueryParser.g4 by ANTLR 4.6
# encoding: utf-8
from __future__ import print_function
from antlr4 import *
from io import StringIO

def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\3")
        buf.write(u"\35\60\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\3\2\6\2\f\n\2")
        buf.write(u"\r\2\16\2\r\3\3\3\3\3\3\7\3\23\n\3\f\3\16\3\26\13\3\3")
        buf.write(u"\4\3\4\3\4\3\4\5\4\34\n\4\3\4\3\4\3\4\3\4\3\4\3\4\3\4")
        buf.write(u"\5\4%\n\4\3\5\3\5\3\5\3\5\3\5\5\5,\n\5\5\5.\n\5\3\5\2")
        buf.write(u"\2\6\2\4\6\b\2\7\3\2\b\t\3\2\22\23\3\2\n\21\4\2\30\31")
        buf.write(u"\34\35\3\2\3\4\63\2\13\3\2\2\2\4\17\3\2\2\2\6$\3\2\2")
        buf.write(u"\2\b-\3\2\2\2\n\f\5\4\3\2\13\n\3\2\2\2\f\r\3\2\2\2\r")
        buf.write(u"\13\3\2\2\2\r\16\3\2\2\2\16\3\3\2\2\2\17\24\5\6\4\2\20")
        buf.write(u"\21\t\2\2\2\21\23\5\6\4\2\22\20\3\2\2\2\23\26\3\2\2\2")
        buf.write(u"\24\22\3\2\2\2\24\25\3\2\2\2\25\5\3\2\2\2\26\24\3\2\2")
        buf.write(u"\2\27\30\7\27\2\2\30\31\t\3\2\2\31%\7\32\2\2\32\34\7")
        buf.write(u"\24\2\2\33\32\3\2\2\2\33\34\3\2\2\2\34\35\3\2\2\2\35")
        buf.write(u"\36\7\27\2\2\36\37\t\4\2\2\37%\5\b\5\2 !\7\6\2\2!\"\5")
        buf.write(u"\4\3\2\"#\7\7\2\2#%\3\2\2\2$\27\3\2\2\2$\33\3\2\2\2$")
        buf.write(u" \3\2\2\2%\7\3\2\2\2&.\7\25\2\2\'.\7\26\2\2(+\t\5\2\2")
        buf.write(u")*\t\6\2\2*,\7\33\2\2+)\3\2\2\2+,\3\2\2\2,.\3\2\2\2-")
        buf.write(u"&\3\2\2\2-\'\3\2\2\2-(\3\2\2\2.\t\3\2\2\2\b\r\24\33$")
        buf.write(u"+-")
        return buf.getvalue()


class QueryParserParser ( Parser ):

    grammarFileName = "QueryParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ u"<INVALID>", u"'+'", u"'-'", u"<INVALID>", u"'('", 
                     u"')'", u"'and'", u"'or'", u"'=='", u"'!='", u"'<'", 
                     u"'<='", u"'>'", u"'>='", u"'~'", u"'under'", u"'is'", 
                     u"'is not'", u"'not'", u"<INVALID>", u"<INVALID>", 
                     u"<INVALID>", u"'@today'", u"'@now'", u"'@none'" ]

    symbolicNames = [ u"<INVALID>", u"<INVALID>", u"<INVALID>", u"WS", u"LPAREN", 
                      u"RPAREN", u"AND", u"OR", u"EQUAL", u"NOT_EQUAL", 
                      u"LT", u"LTE", u"GT", u"GTE", u"LIKE", u"UNDER", u"IS", 
                      u"IS_NOT", u"NOT", u"NUMBER", u"INT", u"ID", u"TODAY", 
                      u"NOW", u"NONE", u"TIME_DELTA", u"DOUBLE_QUOTE_STRING", 
                      u"SINGLE_QUOTE_STRING" ]

    RULE_statements = 0
    RULE_statement = 1
    RULE_expression = 2
    RULE_value = 3

    ruleNames =  [ u"statements", u"statement", u"expression", u"value" ]

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
    IS=16
    IS_NOT=17
    NOT=18
    NUMBER=19
    INT=20
    ID=21
    TODAY=22
    NOW=23
    NONE=24
    TIME_DELTA=25
    DOUBLE_QUOTE_STRING=26
    SINGLE_QUOTE_STRING=27

    def __init__(self, input):
        super(QueryParserParser, self).__init__(input)
        self.checkVersion("4.6")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None



    class StatementsContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(QueryParserParser.StatementsContext, self).__init__(parent, invokingState)
            self.parser = parser

        def statement(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(QueryParserParser.StatementContext)
            else:
                return self.getTypedRuleContext(QueryParserParser.StatementContext,i)


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
            self.state = 9 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 8
                self.statement()
                self.state = 11 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << QueryParserParser.LPAREN) | (1 << QueryParserParser.NOT) | (1 << QueryParserParser.ID))) != 0)):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class StatementContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(QueryParserParser.StatementContext, self).__init__(parent, invokingState)
            self.parser = parser

        def expression(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(QueryParserParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(QueryParserParser.ExpressionContext,i)


        def AND(self, i=None):
            if i is None:
                return self.getTokens(QueryParserParser.AND)
            else:
                return self.getToken(QueryParserParser.AND, i)

        def OR(self, i=None):
            if i is None:
                return self.getTokens(QueryParserParser.OR)
            else:
                return self.getToken(QueryParserParser.OR, i)

        def getRuleIndex(self):
            return QueryParserParser.RULE_statement

        def accept(self, visitor):
            if hasattr(visitor, "visitStatement"):
                return visitor.visitStatement(self)
            else:
                return visitor.visitChildren(self)




    def statement(self):

        localctx = QueryParserParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 13
            self.expression()
            self.state = 18
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==QueryParserParser.AND or _la==QueryParserParser.OR:
                self.state = 14
                _la = self._input.LA(1)
                if not(_la==QueryParserParser.AND or _la==QueryParserParser.OR):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 15
                self.expression()
                self.state = 20
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

        def ID(self):
            return self.getToken(QueryParserParser.ID, 0)

        def NONE(self):
            return self.getToken(QueryParserParser.NONE, 0)

        def value(self):
            return self.getTypedRuleContext(QueryParserParser.ValueContext,0)


        def LPAREN(self):
            return self.getToken(QueryParserParser.LPAREN, 0)

        def statement(self):
            return self.getTypedRuleContext(QueryParserParser.StatementContext,0)


        def RPAREN(self):
            return self.getToken(QueryParserParser.RPAREN, 0)

        def IS(self):
            return self.getToken(QueryParserParser.IS, 0)

        def IS_NOT(self):
            return self.getToken(QueryParserParser.IS_NOT, 0)

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

        def NOT(self):
            return self.getToken(QueryParserParser.NOT, 0)

        def getRuleIndex(self):
            return QueryParserParser.RULE_expression

        def accept(self, visitor):
            if hasattr(visitor, "visitExpression"):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = QueryParserParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_expression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 34
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,3,self._ctx)
            if la_ == 1:
                self.state = 21
                self.match(QueryParserParser.ID)
                self.state = 22
                _la = self._input.LA(1)
                if not(_la==QueryParserParser.IS or _la==QueryParserParser.IS_NOT):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 23
                self.match(QueryParserParser.NONE)
                pass

            elif la_ == 2:
                self.state = 25
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==QueryParserParser.NOT:
                    self.state = 24
                    self.match(QueryParserParser.NOT)


                self.state = 27
                self.match(QueryParserParser.ID)
                self.state = 28
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << QueryParserParser.EQUAL) | (1 << QueryParserParser.NOT_EQUAL) | (1 << QueryParserParser.LT) | (1 << QueryParserParser.LTE) | (1 << QueryParserParser.GT) | (1 << QueryParserParser.GTE) | (1 << QueryParserParser.LIKE) | (1 << QueryParserParser.UNDER))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 29
                self.value()
                pass

            elif la_ == 3:
                self.state = 30
                self.match(QueryParserParser.LPAREN)
                self.state = 31
                self.statement()
                self.state = 32
                self.match(QueryParserParser.RPAREN)
                pass


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
            self.state = 43
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [QueryParserParser.NUMBER]:
                self.enterOuterAlt(localctx, 1)
                self.state = 36
                self.match(QueryParserParser.NUMBER)
                pass
            elif token in [QueryParserParser.INT]:
                self.enterOuterAlt(localctx, 2)
                self.state = 37
                self.match(QueryParserParser.INT)
                pass
            elif token in [QueryParserParser.TODAY, QueryParserParser.NOW, QueryParserParser.DOUBLE_QUOTE_STRING, QueryParserParser.SINGLE_QUOTE_STRING]:
                self.enterOuterAlt(localctx, 3)
                self.state = 38
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << QueryParserParser.TODAY) | (1 << QueryParserParser.NOW) | (1 << QueryParserParser.DOUBLE_QUOTE_STRING) | (1 << QueryParserParser.SINGLE_QUOTE_STRING))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 41
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==QueryParserParser.T__0 or _la==QueryParserParser.T__1:
                    self.state = 39
                    _la = self._input.LA(1)
                    if not(_la==QueryParserParser.T__0 or _la==QueryParserParser.T__1):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()
                    self.state = 40
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





