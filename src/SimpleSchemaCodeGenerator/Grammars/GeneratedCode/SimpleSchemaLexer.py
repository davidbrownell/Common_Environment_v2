# Generated from C:\Code\v2\Common\Environment\src\SimpleSchemaCodeGenerator\Grammars\BuildEnvironment\..\SimpleSchema.g4 by ANTLR 4.5.1
# encoding: utf-8
from __future__ import print_function
from antlr4 import *
from io import StringIO



from CommonEnvironment.Antlr4Helpers.DenterHelper import DenterHelper
from SimpleSchemaParser import SimpleSchemaParser



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\2")
        buf.write(u"D\u02bd\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4")
        buf.write(u"\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r")
        buf.write(u"\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22")
        buf.write(u"\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4")
        buf.write(u"\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4\35")
        buf.write(u"\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t#\4")
        buf.write(u"$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4,\t")
        buf.write(u",\4-\t-\4.\t.\4/\t/\4\60\t\60\4\61\t\61\4\62\t\62\4\63")
        buf.write(u"\t\63\4\64\t\64\4\65\t\65\4\66\t\66\4\67\t\67\48\t8\4")
        buf.write(u"9\t9\4:\t:\4;\t;\4<\t<\4=\t=\4>\t>\4?\t?\4@\t@\4A\tA")
        buf.write(u"\4B\tB\4C\tC\4D\tD\4E\tE\4F\tF\4G\tG\4H\tH\3\2\3\2\5")
        buf.write(u"\2\u0094\n\2\3\2\3\2\3\2\3\2\3\3\3\3\5\3\u009c\n\3\3")
        buf.write(u"\3\3\3\7\3\u00a0\n\3\f\3\16\3\u00a3\13\3\3\4\3\4\5\4")
        buf.write(u"\u00a7\n\4\3\4\3\4\3\4\3\4\3\5\6\5\u00ae\n\5\r\5\16\5")
        buf.write(u"\u00af\3\5\3\5\3\6\3\6\3\6\3\7\3\7\3\7\3\b\3\b\3\b\3")
        buf.write(u"\t\3\t\3\t\3\n\3\n\3\n\3\13\3\13\3\13\3\f\3\f\3\r\3\r")
        buf.write(u"\3\16\3\16\3\16\3\16\7\16\u00ce\n\16\f\16\16\16\u00d1")
        buf.write(u"\13\16\3\16\3\16\3\16\3\16\3\16\3\17\3\17\7\17\u00da")
        buf.write(u"\n\17\f\17\16\17\u00dd\13\17\3\17\3\17\3\20\3\20\3\20")
        buf.write(u"\3\20\3\20\3\21\3\21\3\21\3\21\3\21\3\21\3\21\3\21\3")
        buf.write(u"\22\3\22\3\22\3\22\3\22\3\22\3\22\3\23\3\23\3\23\3\23")
        buf.write(u"\3\23\3\23\3\23\3\24\3\24\3\24\3\24\3\24\3\25\3\25\3")
        buf.write(u"\25\3\25\3\25\3\25\3\25\3\25\3\26\3\26\3\26\3\26\3\26")
        buf.write(u"\3\26\3\26\3\27\3\27\3\27\3\27\3\27\3\27\3\27\3\27\3")
        buf.write(u"\30\3\30\3\30\3\30\3\30\3\31\3\31\3\31\3\31\3\31\3\31")
        buf.write(u"\3\31\3\31\3\31\3\32\3\32\3\32\3\32\3\32\3\33\3\33\3")
        buf.write(u"\33\3\33\3\33\3\34\3\34\3\34\3\34\3\34\3\34\3\34\3\34")
        buf.write(u"\3\34\3\35\3\35\3\35\3\35\3\35\3\35\3\35\3\35\3\35\3")
        buf.write(u"\36\3\36\3\36\3\36\3\36\3\36\3\36\3\37\3\37\3\37\3\37")
        buf.write(u"\3\37\3\37\3\37\3\37\3\37\3\37\3\37\3 \3 \3 \3 \3 \3")
        buf.write(u" \3 \3 \3 \3 \3 \3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3\"")
        buf.write(u"\3\"\3\"\3\"\3\"\3\"\3\"\3#\3#\3#\3#\3#\3#\3#\3#\3#\3")
        buf.write(u"#\3#\3#\3#\3#\3#\3#\3$\3$\3$\3$\3%\3%\3%\3%\3&\3&\3&")
        buf.write(u"\3&\3&\3&\3\'\3\'\3\'\3\'\3\'\3(\3(\3(\3(\3(\3(\3(\3")
        buf.write(u"(\3(\3(\3(\3)\3)\3*\3*\3*\3*\3*\3*\3*\3*\3*\3*\3*\3*")
        buf.write(u"\3+\3+\3+\3+\3+\3+\3+\3,\3,\3,\3,\3,\3,\3,\3,\3-\3-\3")
        buf.write(u"-\3-\3-\3-\3-\3-\3-\3-\3-\3-\3.\3.\3.\3.\3.\3.\3.\3.")
        buf.write(u"\3.\3.\3.\3.\3.\3.\3.\3.\3.\3.\3.\3.\3.\3/\3/\3\60\3")
        buf.write(u"\60\3\61\3\61\3\62\5\62\u01e4\n\62\3\62\6\62\u01e7\n")
        buf.write(u"\62\r\62\16\62\u01e8\3\63\5\63\u01ec\n\63\3\63\7\63\u01ef")
        buf.write(u"\n\63\f\63\16\63\u01f2\13\63\3\63\3\63\6\63\u01f6\n\63")
        buf.write(u"\r\63\16\63\u01f7\3\64\3\64\7\64\u01fc\n\64\f\64\16\64")
        buf.write(u"\u01ff\13\64\3\65\3\65\3\66\3\66\3\67\3\67\38\38\39\3")
        buf.write(u"9\39\39\3:\3:\3:\3:\3;\7;\u0212\n;\f;\16;\u0215\13;\3")
        buf.write(u";\3;\7;\u0219\n;\f;\16;\u021c\13;\3<\3<\3<\3<\3=\3=\3")
        buf.write(u"=\3=\3>\7>\u0227\n>\f>\16>\u022a\13>\3>\3>\7>\u022e\n")
        buf.write(u">\f>\16>\u0231\13>\3?\3?\3?\3?\3@\3@\3@\3@\3A\7A\u023c")
        buf.write(u"\nA\fA\16A\u023f\13A\3A\3A\3A\3A\3A\3A\3A\3A\3A\3A\3")
        buf.write(u"A\3A\3A\3A\3A\3A\3A\3A\5A\u0253\nA\3A\7A\u0256\nA\fA")
        buf.write(u"\16A\u0259\13A\3B\3B\3B\3B\3C\3C\3C\3C\3D\7D\u0264\n")
        buf.write(u"D\fD\16D\u0267\13D\3D\3D\3D\3D\3D\3D\3D\3D\3D\3D\3D\3")
        buf.write(u"D\3D\3D\3D\3D\3D\3D\3D\5D\u027c\nD\3D\7D\u027f\nD\fD")
        buf.write(u"\16D\u0282\13D\3E\3E\3E\3E\3E\5E\u0289\nE\3E\7E\u028c")
        buf.write(u"\nE\fE\16E\u028f\13E\3E\3E\3F\3F\3F\3F\3F\5F\u0298\n")
        buf.write(u"F\3F\7F\u029b\nF\fF\16F\u029e\13F\3F\3F\3G\3G\3G\3G\3")
        buf.write(u"G\7G\u02a7\nG\fG\16G\u02aa\13G\3G\3G\3G\3G\3H\3H\3H\3")
        buf.write(u"H\3H\7H\u02b5\nH\fH\16H\u02b8\13H\3H\3H\3H\3H\7\u00cf")
        buf.write(u"\u028d\u029c\u02a8\u02b6\2I\3\3\5\4\7\5\t\6\13\7\r\b")
        buf.write(u"\17\t\21\n\23\13\25\f\27\r\31\16\33\17\35\20\37\21!\22")
        buf.write(u"#\23%\24\'\25)\26+\27-\30/\31\61\32\63\33\65\34\67\35")
        buf.write(u"9\36;\37= ?!A\"C#E$G%I&K\'M(O)Q*S+U,W-Y.[/]\60_\61a\62")
        buf.write(u"c\63e\64g\65i\66k\67m8o\2q9s:u\2w;y<{\2}=\177>\u0081")
        buf.write(u"\2\u0083?\u0085@\u0087\2\u0089A\u008bB\u008dC\u008fD")
        buf.write(u"\3\2\t\4\2\13\13\"\"\4\2\f\f\17\17\3\2\62;\5\2C\\aac")
        buf.write(u"|\7\2/\60\62;C\\aac|\4\2\63\63{{\4\2\62\62pp\u02dd\2")
        buf.write(u"\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3")
        buf.write(u"\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2")
        buf.write(u"\2\2\2\25\3\2\2\2\2\27\3\2\2\2\2\31\3\2\2\2\2\33\3\2")
        buf.write(u"\2\2\2\35\3\2\2\2\2\37\3\2\2\2\2!\3\2\2\2\2#\3\2\2\2")
        buf.write(u"\2%\3\2\2\2\2\'\3\2\2\2\2)\3\2\2\2\2+\3\2\2\2\2-\3\2")
        buf.write(u"\2\2\2/\3\2\2\2\2\61\3\2\2\2\2\63\3\2\2\2\2\65\3\2\2")
        buf.write(u"\2\2\67\3\2\2\2\29\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2\2?\3")
        buf.write(u"\2\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2\2")
        buf.write(u"I\3\2\2\2\2K\3\2\2\2\2M\3\2\2\2\2O\3\2\2\2\2Q\3\2\2\2")
        buf.write(u"\2S\3\2\2\2\2U\3\2\2\2\2W\3\2\2\2\2Y\3\2\2\2\2[\3\2\2")
        buf.write(u"\2\2]\3\2\2\2\2_\3\2\2\2\2a\3\2\2\2\2c\3\2\2\2\2e\3\2")
        buf.write(u"\2\2\2g\3\2\2\2\2i\3\2\2\2\2k\3\2\2\2\2m\3\2\2\2\2q\3")
        buf.write(u"\2\2\2\2s\3\2\2\2\2w\3\2\2\2\2y\3\2\2\2\2}\3\2\2\2\2")
        buf.write(u"\177\3\2\2\2\2\u0083\3\2\2\2\2\u0085\3\2\2\2\2\u0089")
        buf.write(u"\3\2\2\2\2\u008b\3\2\2\2\2\u008d\3\2\2\2\2\u008f\3\2")
        buf.write(u"\2\2\3\u0091\3\2\2\2\5\u0099\3\2\2\2\7\u00a4\3\2\2\2")
        buf.write(u"\t\u00ad\3\2\2\2\13\u00b3\3\2\2\2\r\u00b6\3\2\2\2\17")
        buf.write(u"\u00b9\3\2\2\2\21\u00bc\3\2\2\2\23\u00bf\3\2\2\2\25\u00c2")
        buf.write(u"\3\2\2\2\27\u00c5\3\2\2\2\31\u00c7\3\2\2\2\33\u00c9\3")
        buf.write(u"\2\2\2\35\u00d7\3\2\2\2\37\u00e0\3\2\2\2!\u00e5\3\2\2")
        buf.write(u"\2#\u00ed\3\2\2\2%\u00f4\3\2\2\2\'\u00fb\3\2\2\2)\u0100")
        buf.write(u"\3\2\2\2+\u0108\3\2\2\2-\u010f\3\2\2\2/\u0117\3\2\2\2")
        buf.write(u"\61\u011c\3\2\2\2\63\u0125\3\2\2\2\65\u012a\3\2\2\2\67")
        buf.write(u"\u012f\3\2\2\29\u0138\3\2\2\2;\u0141\3\2\2\2=\u0148\3")
        buf.write(u"\2\2\2?\u0153\3\2\2\2A\u015e\3\2\2\2C\u0169\3\2\2\2E")
        buf.write(u"\u0170\3\2\2\2G\u0180\3\2\2\2I\u0184\3\2\2\2K\u0188\3")
        buf.write(u"\2\2\2M\u018e\3\2\2\2O\u0193\3\2\2\2Q\u019e\3\2\2\2S")
        buf.write(u"\u01a0\3\2\2\2U\u01ac\3\2\2\2W\u01b3\3\2\2\2Y\u01bb\3")
        buf.write(u"\2\2\2[\u01c7\3\2\2\2]\u01dc\3\2\2\2_\u01de\3\2\2\2a")
        buf.write(u"\u01e0\3\2\2\2c\u01e3\3\2\2\2e\u01eb\3\2\2\2g\u01f9\3")
        buf.write(u"\2\2\2i\u0200\3\2\2\2k\u0202\3\2\2\2m\u0204\3\2\2\2o")
        buf.write(u"\u0206\3\2\2\2q\u0208\3\2\2\2s\u020c\3\2\2\2u\u0213\3")
        buf.write(u"\2\2\2w\u021d\3\2\2\2y\u0221\3\2\2\2{\u0228\3\2\2\2}")
        buf.write(u"\u0232\3\2\2\2\177\u0236\3\2\2\2\u0081\u023d\3\2\2\2")
        buf.write(u"\u0083\u025a\3\2\2\2\u0085\u025e\3\2\2\2\u0087\u0265")
        buf.write(u"\3\2\2\2\u0089\u0283\3\2\2\2\u008b\u0292\3\2\2\2\u008d")
        buf.write(u"\u02a1\3\2\2\2\u008f\u02af\3\2\2\2\u0091\u0093\6\2\2")
        buf.write(u"\2\u0092\u0094\7\17\2\2\u0093\u0092\3\2\2\2\u0093\u0094")
        buf.write(u"\3\2\2\2\u0094\u0095\3\2\2\2\u0095\u0096\7\f\2\2\u0096")
        buf.write(u"\u0097\3\2\2\2\u0097\u0098\b\2\2\2\u0098\4\3\2\2\2\u0099")
        buf.write(u"\u009b\6\3\3\2\u009a\u009c\7\17\2\2\u009b\u009a\3\2\2")
        buf.write(u"\2\u009b\u009c\3\2\2\2\u009c\u009d\3\2\2\2\u009d\u00a1")
        buf.write(u"\7\f\2\2\u009e\u00a0\t\2\2\2\u009f\u009e\3\2\2\2\u00a0")
        buf.write(u"\u00a3\3\2\2\2\u00a1\u009f\3\2\2\2\u00a1\u00a2\3\2\2")
        buf.write(u"\2\u00a2\6\3\2\2\2\u00a3\u00a1\3\2\2\2\u00a4\u00a6\7")
        buf.write(u"^\2\2\u00a5\u00a7\7\17\2\2\u00a6\u00a5\3\2\2\2\u00a6")
        buf.write(u"\u00a7\3\2\2\2\u00a7\u00a8\3\2\2\2\u00a8\u00a9\7\f\2")
        buf.write(u"\2\u00a9\u00aa\3\2\2\2\u00aa\u00ab\b\4\2\2\u00ab\b\3")
        buf.write(u"\2\2\2\u00ac\u00ae\t\2\2\2\u00ad\u00ac\3\2\2\2\u00ae")
        buf.write(u"\u00af\3\2\2\2\u00af\u00ad\3\2\2\2\u00af\u00b0\3\2\2")
        buf.write(u"\2\u00b0\u00b1\3\2\2\2\u00b1\u00b2\b\5\2\2\u00b2\n\3")
        buf.write(u"\2\2\2\u00b3\u00b4\7*\2\2\u00b4\u00b5\b\6\3\2\u00b5\f")
        buf.write(u"\3\2\2\2\u00b6\u00b7\7+\2\2\u00b7\u00b8\b\7\4\2\u00b8")
        buf.write(u"\16\3\2\2\2\u00b9\u00ba\7]\2\2\u00ba\u00bb\b\b\5\2\u00bb")
        buf.write(u"\20\3\2\2\2\u00bc\u00bd\7_\2\2\u00bd\u00be\b\t\6\2\u00be")
        buf.write(u"\22\3\2\2\2\u00bf\u00c0\7>\2\2\u00c0\u00c1\b\n\7\2\u00c1")
        buf.write(u"\24\3\2\2\2\u00c2\u00c3\7@\2\2\u00c3\u00c4\b\13\b\2\u00c4")
        buf.write(u"\26\3\2\2\2\u00c5\u00c6\7}\2\2\u00c6\30\3\2\2\2\u00c7")
        buf.write(u"\u00c8\7\177\2\2\u00c8\32\3\2\2\2\u00c9\u00ca\7%\2\2")
        buf.write(u"\u00ca\u00cb\7\61\2\2\u00cb\u00cf\3\2\2\2\u00cc\u00ce")
        buf.write(u"\13\2\2\2\u00cd\u00cc\3\2\2\2\u00ce\u00d1\3\2\2\2\u00cf")
        buf.write(u"\u00d0\3\2\2\2\u00cf\u00cd\3\2\2\2\u00d0\u00d2\3\2\2")
        buf.write(u"\2\u00d1\u00cf\3\2\2\2\u00d2\u00d3\7\61\2\2\u00d3\u00d4")
        buf.write(u"\7%\2\2\u00d4\u00d5\3\2\2\2\u00d5\u00d6\b\16\2\2\u00d6")
        buf.write(u"\34\3\2\2\2\u00d7\u00db\7%\2\2\u00d8\u00da\n\3\2\2\u00d9")
        buf.write(u"\u00d8\3\2\2\2\u00da\u00dd\3\2\2\2\u00db\u00d9\3\2\2")
        buf.write(u"\2\u00db\u00dc\3\2\2\2\u00dc\u00de\3\2\2\2\u00dd\u00db")
        buf.write(u"\3\2\2\2\u00de\u00df\b\17\2\2\u00df\36\3\2\2\2\u00e0")
        buf.write(u"\u00e1\7r\2\2\u00e1\u00e2\7c\2\2\u00e2\u00e3\7u\2\2\u00e3")
        buf.write(u"\u00e4\7u\2\2\u00e4 \3\2\2\2\u00e5\u00e6\7k\2\2\u00e6")
        buf.write(u"\u00e7\7p\2\2\u00e7\u00e8\7e\2\2\u00e8\u00e9\7n\2\2\u00e9")
        buf.write(u"\u00ea\7w\2\2\u00ea\u00eb\7f\2\2\u00eb\u00ec\7g\2\2\u00ec")
        buf.write(u"\"\3\2\2\2\u00ed\u00ee\7e\2\2\u00ee\u00ef\7q\2\2\u00ef")
        buf.write(u"\u00f0\7p\2\2\u00f0\u00f1\7h\2\2\u00f1\u00f2\7k\2\2\u00f2")
        buf.write(u"\u00f3\7i\2\2\u00f3$\3\2\2\2\u00f4\u00f5\7u\2\2\u00f5")
        buf.write(u"\u00f6\7v\2\2\u00f6\u00f7\7t\2\2\u00f7\u00f8\7k\2\2\u00f8")
        buf.write(u"\u00f9\7p\2\2\u00f9\u00fa\7i\2\2\u00fa&\3\2\2\2\u00fb")
        buf.write(u"\u00fc\7g\2\2\u00fc\u00fd\7p\2\2\u00fd\u00fe\7w\2\2\u00fe")
        buf.write(u"\u00ff\7o\2\2\u00ff(\3\2\2\2\u0100\u0101\7k\2\2\u0101")
        buf.write(u"\u0102\7p\2\2\u0102\u0103\7v\2\2\u0103\u0104\7g\2\2\u0104")
        buf.write(u"\u0105\7i\2\2\u0105\u0106\7g\2\2\u0106\u0107\7t\2\2\u0107")
        buf.write(u"*\3\2\2\2\u0108\u0109\7p\2\2\u0109\u010a\7w\2\2\u010a")
        buf.write(u"\u010b\7o\2\2\u010b\u010c\7d\2\2\u010c\u010d\7g\2\2\u010d")
        buf.write(u"\u010e\7t\2\2\u010e,\3\2\2\2\u010f\u0110\7d\2\2\u0110")
        buf.write(u"\u0111\7q\2\2\u0111\u0112\7q\2\2\u0112\u0113\7n\2\2\u0113")
        buf.write(u"\u0114\7g\2\2\u0114\u0115\7c\2\2\u0115\u0116\7p\2\2\u0116")
        buf.write(u".\3\2\2\2\u0117\u0118\7i\2\2\u0118\u0119\7w\2\2\u0119")
        buf.write(u"\u011a\7k\2\2\u011a\u011b\7f\2\2\u011b\60\3\2\2\2\u011c")
        buf.write(u"\u011d\7f\2\2\u011d\u011e\7c\2\2\u011e\u011f\7v\2\2\u011f")
        buf.write(u"\u0120\7g\2\2\u0120\u0121\7v\2\2\u0121\u0122\7k\2\2\u0122")
        buf.write(u"\u0123\7o\2\2\u0123\u0124\7g\2\2\u0124\62\3\2\2\2\u0125")
        buf.write(u"\u0126\7f\2\2\u0126\u0127\7c\2\2\u0127\u0128\7v\2\2\u0128")
        buf.write(u"\u0129\7g\2\2\u0129\64\3\2\2\2\u012a\u012b\7v\2\2\u012b")
        buf.write(u"\u012c\7k\2\2\u012c\u012d\7o\2\2\u012d\u012e\7g\2\2\u012e")
        buf.write(u"\66\3\2\2\2\u012f\u0130\7f\2\2\u0130\u0131\7w\2\2\u0131")
        buf.write(u"\u0132\7t\2\2\u0132\u0133\7c\2\2\u0133\u0134\7v\2\2\u0134")
        buf.write(u"\u0135\7k\2\2\u0135\u0136\7q\2\2\u0136\u0137\7p\2\2\u0137")
        buf.write(u"8\3\2\2\2\u0138\u0139\7h\2\2\u0139\u013a\7k\2\2\u013a")
        buf.write(u"\u013b\7n\2\2\u013b\u013c\7g\2\2\u013c\u013d\7p\2\2\u013d")
        buf.write(u"\u013e\7c\2\2\u013e\u013f\7o\2\2\u013f\u0140\7g\2\2\u0140")
        buf.write(u":\3\2\2\2\u0141\u0142\7e\2\2\u0142\u0143\7w\2\2\u0143")
        buf.write(u"\u0144\7u\2\2\u0144\u0145\7v\2\2\u0145\u0146\7q\2\2\u0146")
        buf.write(u"\u0147\7o\2\2\u0147<\3\2\2\2\u0148\u0149\7x\2\2\u0149")
        buf.write(u"\u014a\7c\2\2\u014a\u014b\7n\2\2\u014b\u014c\7k\2\2\u014c")
        buf.write(u"\u014d\7f\2\2\u014d\u014e\7c\2\2\u014e\u014f\7v\2\2\u014f")
        buf.write(u"\u0150\7k\2\2\u0150\u0151\7q\2\2\u0151\u0152\7p\2\2\u0152")
        buf.write(u">\3\2\2\2\u0153\u0154\7o\2\2\u0154\u0155\7k\2\2\u0155")
        buf.write(u"\u0156\7p\2\2\u0156\u0157\7a\2\2\u0157\u0158\7n\2\2\u0158")
        buf.write(u"\u0159\7g\2\2\u0159\u015a\7p\2\2\u015a\u015b\7i\2\2\u015b")
        buf.write(u"\u015c\7v\2\2\u015c\u015d\7j\2\2\u015d@\3\2\2\2\u015e")
        buf.write(u"\u015f\7o\2\2\u015f\u0160\7c\2\2\u0160\u0161\7z\2\2\u0161")
        buf.write(u"\u0162\7a\2\2\u0162\u0163\7n\2\2\u0163\u0164\7g\2\2\u0164")
        buf.write(u"\u0165\7p\2\2\u0165\u0166\7i\2\2\u0166\u0167\7v\2\2\u0167")
        buf.write(u"\u0168\7j\2\2\u0168B\3\2\2\2\u0169\u016a\7x\2\2\u016a")
        buf.write(u"\u016b\7c\2\2\u016b\u016c\7n\2\2\u016c\u016d\7w\2\2\u016d")
        buf.write(u"\u016e\7g\2\2\u016e\u016f\7u\2\2\u016fD\3\2\2\2\u0170")
        buf.write(u"\u0171\7h\2\2\u0171\u0172\7t\2\2\u0172\u0173\7k\2\2\u0173")
        buf.write(u"\u0174\7g\2\2\u0174\u0175\7p\2\2\u0175\u0176\7f\2\2\u0176")
        buf.write(u"\u0177\7n\2\2\u0177\u0178\7{\2\2\u0178\u0179\7a\2\2\u0179")
        buf.write(u"\u017a\7x\2\2\u017a\u017b\7c\2\2\u017b\u017c\7n\2\2\u017c")
        buf.write(u"\u017d\7w\2\2\u017d\u017e\7g\2\2\u017e\u017f\7u\2\2\u017f")
        buf.write(u"F\3\2\2\2\u0180\u0181\7o\2\2\u0181\u0182\7k\2\2\u0182")
        buf.write(u"\u0183\7p\2\2\u0183H\3\2\2\2\u0184\u0185\7o\2\2\u0185")
        buf.write(u"\u0186\7c\2\2\u0186\u0187\7z\2\2\u0187J\3\2\2\2\u0188")
        buf.write(u"\u0189\7d\2\2\u0189\u018a\7{\2\2\u018a\u018b\7v\2\2\u018b")
        buf.write(u"\u018c\7g\2\2\u018c\u018d\7u\2\2\u018dL\3\2\2\2\u018e")
        buf.write(u"\u018f\7v\2\2\u018f\u0190\7{\2\2\u0190\u0191\7r\2\2\u0191")
        buf.write(u"\u0192\7g\2\2\u0192N\3\2\2\2\u0193\u0194\7o\2\2\u0194")
        buf.write(u"\u0195\7w\2\2\u0195\u0196\7u\2\2\u0196\u0197\7v\2\2\u0197")
        buf.write(u"\u0198\7a\2\2\u0198\u0199\7g\2\2\u0199\u019a\7z\2\2\u019a")
        buf.write(u"\u019b\7k\2\2\u019b\u019c\7u\2\2\u019c\u019d\7v\2\2\u019d")
        buf.write(u"P\3\2\2\2\u019e\u019f\7v\2\2\u019fR\3\2\2\2\u01a0\u01a1")
        buf.write(u"\7f\2\2\u01a1\u01a2\7g\2\2\u01a2\u01a3\7u\2\2\u01a3\u01a4")
        buf.write(u"\7e\2\2\u01a4\u01a5\7t\2\2\u01a5\u01a6\7k\2\2\u01a6\u01a7")
        buf.write(u"\7r\2\2\u01a7\u01a8\7v\2\2\u01a8\u01a9\7k\2\2\u01a9\u01aa")
        buf.write(u"\7q\2\2\u01aa\u01ab\7p\2\2\u01abT\3\2\2\2\u01ac\u01ad")
        buf.write(u"\7r\2\2\u01ad\u01ae\7n\2\2\u01ae\u01af\7w\2\2\u01af\u01b0")
        buf.write(u"\7t\2\2\u01b0\u01b1\7c\2\2\u01b1\u01b2\7n\2\2\u01b2V")
        buf.write(u"\3\2\2\2\u01b3\u01b4\7f\2\2\u01b4\u01b5\7g\2\2\u01b5")
        buf.write(u"\u01b6\7h\2\2\u01b6\u01b7\7c\2\2\u01b7\u01b8\7w\2\2\u01b8")
        buf.write(u"\u01b9\7n\2\2\u01b9\u01ba\7v\2\2\u01baX\3\2\2\2\u01bb")
        buf.write(u"\u01bc\7r\2\2\u01bc\u01bd\7q\2\2\u01bd\u01be\7n\2\2\u01be")
        buf.write(u"\u01bf\7{\2\2\u01bf\u01c0\7o\2\2\u01c0\u01c1\7q\2\2\u01c1")
        buf.write(u"\u01c2\7t\2\2\u01c2\u01c3\7r\2\2\u01c3\u01c4\7j\2\2\u01c4")
        buf.write(u"\u01c5\7k\2\2\u01c5\u01c6\7e\2\2\u01c6Z\3\2\2\2\u01c7")
        buf.write(u"\u01c8\7u\2\2\u01c8\u01c9\7w\2\2\u01c9\u01ca\7r\2\2\u01ca")
        buf.write(u"\u01cb\7r\2\2\u01cb\u01cc\7t\2\2\u01cc\u01cd\7g\2\2\u01cd")
        buf.write(u"\u01ce\7u\2\2\u01ce\u01cf\7u\2\2\u01cf\u01d0\7a\2\2\u01d0")
        buf.write(u"\u01d1\7r\2\2\u01d1\u01d2\7q\2\2\u01d2\u01d3\7n\2\2\u01d3")
        buf.write(u"\u01d4\7{\2\2\u01d4\u01d5\7o\2\2\u01d5\u01d6\7q\2\2\u01d6")
        buf.write(u"\u01d7\7t\2\2\u01d7\u01d8\7r\2\2\u01d8\u01d9\7j\2\2\u01d9")
        buf.write(u"\u01da\7k\2\2\u01da\u01db\7e\2\2\u01db\\\3\2\2\2\u01dc")
        buf.write(u"\u01dd\7<\2\2\u01dd^\3\2\2\2\u01de\u01df\7?\2\2\u01df")
        buf.write(u"`\3\2\2\2\u01e0\u01e1\7.\2\2\u01e1b\3\2\2\2\u01e2\u01e4")
        buf.write(u"\7/\2\2\u01e3\u01e2\3\2\2\2\u01e3\u01e4\3\2\2\2\u01e4")
        buf.write(u"\u01e6\3\2\2\2\u01e5\u01e7\t\4\2\2\u01e6\u01e5\3\2\2")
        buf.write(u"\2\u01e7\u01e8\3\2\2\2\u01e8\u01e6\3\2\2\2\u01e8\u01e9")
        buf.write(u"\3\2\2\2\u01e9d\3\2\2\2\u01ea\u01ec\7/\2\2\u01eb\u01ea")
        buf.write(u"\3\2\2\2\u01eb\u01ec\3\2\2\2\u01ec\u01f0\3\2\2\2\u01ed")
        buf.write(u"\u01ef\t\4\2\2\u01ee\u01ed\3\2\2\2\u01ef\u01f2\3\2\2")
        buf.write(u"\2\u01f0\u01ee\3\2\2\2\u01f0\u01f1\3\2\2\2\u01f1\u01f3")
        buf.write(u"\3\2\2\2\u01f2\u01f0\3\2\2\2\u01f3\u01f5\7\60\2\2\u01f4")
        buf.write(u"\u01f6\t\4\2\2\u01f5\u01f4\3\2\2\2\u01f6\u01f7\3\2\2")
        buf.write(u"\2\u01f7\u01f5\3\2\2\2\u01f7\u01f8\3\2\2\2\u01f8f\3\2")
        buf.write(u"\2\2\u01f9\u01fd\t\5\2\2\u01fa\u01fc\t\6\2\2\u01fb\u01fa")
        buf.write(u"\3\2\2\2\u01fc\u01ff\3\2\2\2\u01fd\u01fb\3\2\2\2\u01fd")
        buf.write(u"\u01fe\3\2\2\2\u01feh\3\2\2\2\u01ff\u01fd\3\2\2\2\u0200")
        buf.write(u"\u0201\7A\2\2\u0201j\3\2\2\2\u0202\u0203\7,\2\2\u0203")
        buf.write(u"l\3\2\2\2\u0204\u0205\7-\2\2\u0205n\3\2\2\2\u0206\u0207")
        buf.write(u"\t\2\2\2\u0207p\3\2\2\2\u0208\u0209\7$\2\2\u0209\u020a")
        buf.write(u"\5u;\2\u020a\u020b\7$\2\2\u020br\3\2\2\2\u020c\u020d")
        buf.write(u"\7)\2\2\u020d\u020e\5u;\2\u020e\u020f\7)\2\2\u020ft\3")
        buf.write(u"\2\2\2\u0210\u0212\5o8\2\u0211\u0210\3\2\2\2\u0212\u0215")
        buf.write(u"\3\2\2\2\u0213\u0211\3\2\2\2\u0213\u0214\3\2\2\2\u0214")
        buf.write(u"\u0216\3\2\2\2\u0215\u0213\3\2\2\2\u0216\u021a\5e\63")
        buf.write(u"\2\u0217\u0219\5o8\2\u0218\u0217\3\2\2\2\u0219\u021c")
        buf.write(u"\3\2\2\2\u021a\u0218\3\2\2\2\u021a\u021b\3\2\2\2\u021b")
        buf.write(u"v\3\2\2\2\u021c\u021a\3\2\2\2\u021d\u021e\7$\2\2\u021e")
        buf.write(u"\u021f\5{>\2\u021f\u0220\7$\2\2\u0220x\3\2\2\2\u0221")
        buf.write(u"\u0222\7)\2\2\u0222\u0223\5{>\2\u0223\u0224\7)\2\2\u0224")
        buf.write(u"z\3\2\2\2\u0225\u0227\5o8\2\u0226\u0225\3\2\2\2\u0227")
        buf.write(u"\u022a\3\2\2\2\u0228\u0226\3\2\2\2\u0228\u0229\3\2\2")
        buf.write(u"\2\u0229\u022b\3\2\2\2\u022a\u0228\3\2\2\2\u022b\u022f")
        buf.write(u"\5c\62\2\u022c\u022e\5o8\2\u022d\u022c\3\2\2\2\u022e")
        buf.write(u"\u0231\3\2\2\2\u022f\u022d\3\2\2\2\u022f\u0230\3\2\2")
        buf.write(u"\2\u0230|\3\2\2\2\u0231\u022f\3\2\2\2\u0232\u0233\7$")
        buf.write(u"\2\2\u0233\u0234\5\u0081A\2\u0234\u0235\7$\2\2\u0235")
        buf.write(u"~\3\2\2\2\u0236\u0237\7)\2\2\u0237\u0238\5\u0081A\2\u0238")
        buf.write(u"\u0239\7)\2\2\u0239\u0080\3\2\2\2\u023a\u023c\5o8\2\u023b")
        buf.write(u"\u023a\3\2\2\2\u023c\u023f\3\2\2\2\u023d\u023b\3\2\2")
        buf.write(u"\2\u023d\u023e\3\2\2\2\u023e\u0252\3\2\2\2\u023f\u023d")
        buf.write(u"\3\2\2\2\u0240\u0241\7v\2\2\u0241\u0242\7t\2\2\u0242")
        buf.write(u"\u0243\7w\2\2\u0243\u0253\7g\2\2\u0244\u0253\7v\2\2\u0245")
        buf.write(u"\u0246\7{\2\2\u0246\u0247\7g\2\2\u0247\u0253\7u\2\2\u0248")
        buf.write(u"\u0253\t\7\2\2\u0249\u024a\7h\2\2\u024a\u024b\7c\2\2")
        buf.write(u"\u024b\u024c\7n\2\2\u024c\u024d\7u\2\2\u024d\u0253\7")
        buf.write(u"g\2\2\u024e\u0253\7h\2\2\u024f\u0250\7p\2\2\u0250\u0253")
        buf.write(u"\7q\2\2\u0251\u0253\t\b\2\2\u0252\u0240\3\2\2\2\u0252")
        buf.write(u"\u0244\3\2\2\2\u0252\u0245\3\2\2\2\u0252\u0248\3\2\2")
        buf.write(u"\2\u0252\u0249\3\2\2\2\u0252\u024e\3\2\2\2\u0252\u024f")
        buf.write(u"\3\2\2\2\u0252\u0251\3\2\2\2\u0253\u0257\3\2\2\2\u0254")
        buf.write(u"\u0256\5o8\2\u0255\u0254\3\2\2\2\u0256\u0259\3\2\2\2")
        buf.write(u"\u0257\u0255\3\2\2\2\u0257\u0258\3\2\2\2\u0258\u0082")
        buf.write(u"\3\2\2\2\u0259\u0257\3\2\2\2\u025a\u025b\7$\2\2\u025b")
        buf.write(u"\u025c\5\u0087D\2\u025c\u025d\7$\2\2\u025d\u0084\3\2")
        buf.write(u"\2\2\u025e\u025f\7)\2\2\u025f\u0260\5\u0087D\2\u0260")
        buf.write(u"\u0261\7)\2\2\u0261\u0086\3\2\2\2\u0262\u0264\5o8\2\u0263")
        buf.write(u"\u0262\3\2\2\2\u0264\u0267\3\2\2\2\u0265\u0263\3\2\2")
        buf.write(u"\2\u0265\u0266\3\2\2\2\u0266\u027b\3\2\2\2\u0267\u0265")
        buf.write(u"\3\2\2\2\u0268\u0269\7h\2\2\u0269\u026a\7k\2\2\u026a")
        buf.write(u"\u026b\7n\2\2\u026b\u027c\7g\2\2\u026c\u026d\7f\2\2\u026d")
        buf.write(u"\u026e\7k\2\2\u026e\u026f\7t\2\2\u026f\u0270\7g\2\2\u0270")
        buf.write(u"\u0271\7e\2\2\u0271\u0272\7v\2\2\u0272\u0273\7q\2\2\u0273")
        buf.write(u"\u0274\7t\2\2\u0274\u027c\7{\2\2\u0275\u0276\7g\2\2\u0276")
        buf.write(u"\u0277\7k\2\2\u0277\u0278\7v\2\2\u0278\u0279\7j\2\2\u0279")
        buf.write(u"\u027a\7g\2\2\u027a\u027c\7t\2\2\u027b\u0268\3\2\2\2")
        buf.write(u"\u027b\u026c\3\2\2\2\u027b\u0275\3\2\2\2\u027c\u0280")
        buf.write(u"\3\2\2\2\u027d\u027f\5o8\2\u027e\u027d\3\2\2\2\u027f")
        buf.write(u"\u0282\3\2\2\2\u0280\u027e\3\2\2\2\u0280\u0281\3\2\2")
        buf.write(u"\2\u0281\u0088\3\2\2\2\u0282\u0280\3\2\2\2\u0283\u028d")
        buf.write(u"\7$\2\2\u0284\u0285\7^\2\2\u0285\u0289\7$\2\2\u0286\u0287")
        buf.write(u"\7^\2\2\u0287\u0289\7^\2\2\u0288\u0284\3\2\2\2\u0288")
        buf.write(u"\u0286\3\2\2\2\u0289\u028c\3\2\2\2\u028a\u028c\13\2\2")
        buf.write(u"\2\u028b\u0288\3\2\2\2\u028b\u028a\3\2\2\2\u028c\u028f")
        buf.write(u"\3\2\2\2\u028d\u028e\3\2\2\2\u028d\u028b\3\2\2\2\u028e")
        buf.write(u"\u0290\3\2\2\2\u028f\u028d\3\2\2\2\u0290\u0291\7$\2\2")
        buf.write(u"\u0291\u008a\3\2\2\2\u0292\u029c\7)\2\2\u0293\u0294\7")
        buf.write(u"^\2\2\u0294\u0298\7)\2\2\u0295\u0296\7^\2\2\u0296\u0298")
        buf.write(u"\7^\2\2\u0297\u0293\3\2\2\2\u0297\u0295\3\2\2\2\u0298")
        buf.write(u"\u029b\3\2\2\2\u0299\u029b\13\2\2\2\u029a\u0297\3\2\2")
        buf.write(u"\2\u029a\u0299\3\2\2\2\u029b\u029e\3\2\2\2\u029c\u029d")
        buf.write(u"\3\2\2\2\u029c\u029a\3\2\2\2\u029d\u029f\3\2\2\2\u029e")
        buf.write(u"\u029c\3\2\2\2\u029f\u02a0\7)\2\2\u02a0\u008c\3\2\2\2")
        buf.write(u"\u02a1\u02a2\7$\2\2\u02a2\u02a3\7$\2\2\u02a3\u02a4\7")
        buf.write(u"$\2\2\u02a4\u02a8\3\2\2\2\u02a5\u02a7\13\2\2\2\u02a6")
        buf.write(u"\u02a5\3\2\2\2\u02a7\u02aa\3\2\2\2\u02a8\u02a9\3\2\2")
        buf.write(u"\2\u02a8\u02a6\3\2\2\2\u02a9\u02ab\3\2\2\2\u02aa\u02a8")
        buf.write(u"\3\2\2\2\u02ab\u02ac\7$\2\2\u02ac\u02ad\7$\2\2\u02ad")
        buf.write(u"\u02ae\7$\2\2\u02ae\u008e\3\2\2\2\u02af\u02b0\7)\2\2")
        buf.write(u"\u02b0\u02b1\7)\2\2\u02b1\u02b2\7)\2\2\u02b2\u02b6\3")
        buf.write(u"\2\2\2\u02b3\u02b5\13\2\2\2\u02b4\u02b3\3\2\2\2\u02b5")
        buf.write(u"\u02b8\3\2\2\2\u02b6\u02b7\3\2\2\2\u02b6\u02b4\3\2\2")
        buf.write(u"\2\u02b7\u02b9\3\2\2\2\u02b8\u02b6\3\2\2\2\u02b9\u02ba")
        buf.write(u"\7)\2\2\u02ba\u02bb\7)\2\2\u02bb\u02bc\7)\2\2\u02bc\u0090")
        buf.write(u"\3\2\2\2\"\2\u0093\u009b\u00a1\u00a6\u00af\u00cf\u00db")
        buf.write(u"\u01e3\u01e8\u01eb\u01f0\u01f7\u01fd\u0213\u021a\u0228")
        buf.write(u"\u022f\u023d\u0252\u0257\u0265\u027b\u0280\u0288\u028b")
        buf.write(u"\u028d\u0297\u029a\u029c\u02a8\u02b6\t\b\2\2\3\6\2\3")
        buf.write(u"\7\3\3\b\4\3\t\5\3\n\6\3\13\7")
        return buf.getvalue()


class SimpleSchemaLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]


    MULTI_LINE_NEWLINE = 1
    NEWLINE = 2
    MULTI_LINE_ESCAPE = 3
    HORIZONTAL_WHITESPACE = 4
    LPAREN = 5
    RPAREN = 6
    LBRACK = 7
    RBRACK = 8
    LT = 9
    GT = 10
    LBRACE = 11
    RBRACE = 12
    MULTI_LINE_COMMENT = 13
    COMMENT = 14
    PASS = 15
    INCLUDE = 16
    CONFIG = 17
    STRING_TYPE = 18
    ENUM_TYPE = 19
    INTEGER_TYPE = 20
    NUMBER_TYPE = 21
    BOOLEAN_TYPE = 22
    GUID_TYPE = 23
    DATETIME_TYPE = 24
    DATE_TYPE = 25
    TIME_TYPE = 26
    DURATION_TYPE = 27
    FILENAME_TYPE = 28
    CUSTOM_TYPE = 29
    STRING_METADATA_VALIDATION = 30
    STRING_METADATA_MIN_LENGTH = 31
    STRING_METADATA_MAX_LENGTH = 32
    ENUM_METADATA_VALUES = 33
    ENUM_METADATA_FRIENDLY_VALUES = 34
    METADATA_MIN = 35
    METADATA_MAX = 36
    INTEGER_METADATA_BYTES = 37
    FILENAME_METADATA_TYPE = 38
    FILENAME_METADATA_MUST_EXIST = 39
    CUSTOM_METADATA_T = 40
    GENERIC_METADATA_DESCRIPTION = 41
    GENERIC_METADATA_PLURAL = 42
    GENERIC_METADATA_DEFAULT = 43
    GENERIC_METADATA_POLYMORPHIC = 44
    GENERIC_METADATA_SUPPRESS_POLYMORPHIC = 45
    SCOPE_DELIMITER = 46
    ASSIGNMENT = 47
    COMMA = 48
    INT = 49
    NUMBER = 50
    ID = 51
    ARITY_OPTIONAL = 52
    ARITY_ZERO_OR_MORE = 53
    ARITY_ONE_OR_MORE = 54
    DOUBLE_QUOTE_NUMBER = 55
    SINGLE_QUOTE_NUMBER = 56
    DOUBLE_QUOTE_INT = 57
    SINGLE_QUOTE_INT = 58
    DOUBLE_QUOTE_BOOL = 59
    SINGLE_QUOTE_BOOL = 60
    DOUBLE_QUOTE_FILENAME_TYPE = 61
    SINGLE_QUOTE_FILENAME_TYPE = 62
    DOUBLE_QUOTE_STRING = 63
    SINGLE_QUOTE_STRING = 64
    TRIPLE_DOUBLE_QUOTE_STRING = 65
    TRIPLE_SINGLE_QUOTE_STRING = 66

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'('", u"')'", u"'['", u"']'", u"'<'", u"'>'", u"'{'", u"'}'", 
            u"'pass'", u"'include'", u"'config'", u"'string'", u"'enum'", 
            u"'integer'", u"'number'", u"'boolean'", u"'guid'", u"'datetime'", 
            u"'date'", u"'time'", u"'duration'", u"'filename'", u"'custom'", 
            u"'validation'", u"'min_length'", u"'max_length'", u"'values'", 
            u"'friendly_values'", u"'min'", u"'max'", u"'bytes'", u"'type'", 
            u"'must_exist'", u"'t'", u"'description'", u"'plural'", u"'default'", 
            u"'polymorphic'", u"'suppress_polymorphic'", u"':'", u"'='", 
            u"','", u"'?'", u"'*'", u"'+'" ]

    symbolicNames = [ u"<INVALID>",
            u"MULTI_LINE_NEWLINE", u"NEWLINE", u"MULTI_LINE_ESCAPE", u"HORIZONTAL_WHITESPACE", 
            u"LPAREN", u"RPAREN", u"LBRACK", u"RBRACK", u"LT", u"GT", u"LBRACE", 
            u"RBRACE", u"MULTI_LINE_COMMENT", u"COMMENT", u"PASS", u"INCLUDE", 
            u"CONFIG", u"STRING_TYPE", u"ENUM_TYPE", u"INTEGER_TYPE", u"NUMBER_TYPE", 
            u"BOOLEAN_TYPE", u"GUID_TYPE", u"DATETIME_TYPE", u"DATE_TYPE", 
            u"TIME_TYPE", u"DURATION_TYPE", u"FILENAME_TYPE", u"CUSTOM_TYPE", 
            u"STRING_METADATA_VALIDATION", u"STRING_METADATA_MIN_LENGTH", 
            u"STRING_METADATA_MAX_LENGTH", u"ENUM_METADATA_VALUES", u"ENUM_METADATA_FRIENDLY_VALUES", 
            u"METADATA_MIN", u"METADATA_MAX", u"INTEGER_METADATA_BYTES", 
            u"FILENAME_METADATA_TYPE", u"FILENAME_METADATA_MUST_EXIST", 
            u"CUSTOM_METADATA_T", u"GENERIC_METADATA_DESCRIPTION", u"GENERIC_METADATA_PLURAL", 
            u"GENERIC_METADATA_DEFAULT", u"GENERIC_METADATA_POLYMORPHIC", 
            u"GENERIC_METADATA_SUPPRESS_POLYMORPHIC", u"SCOPE_DELIMITER", 
            u"ASSIGNMENT", u"COMMA", u"INT", u"NUMBER", u"ID", u"ARITY_OPTIONAL", 
            u"ARITY_ZERO_OR_MORE", u"ARITY_ONE_OR_MORE", u"DOUBLE_QUOTE_NUMBER", 
            u"SINGLE_QUOTE_NUMBER", u"DOUBLE_QUOTE_INT", u"SINGLE_QUOTE_INT", 
            u"DOUBLE_QUOTE_BOOL", u"SINGLE_QUOTE_BOOL", u"DOUBLE_QUOTE_FILENAME_TYPE", 
            u"SINGLE_QUOTE_FILENAME_TYPE", u"DOUBLE_QUOTE_STRING", u"SINGLE_QUOTE_STRING", 
            u"TRIPLE_DOUBLE_QUOTE_STRING", u"TRIPLE_SINGLE_QUOTE_STRING" ]

    ruleNames = [ u"MULTI_LINE_NEWLINE", u"NEWLINE", u"MULTI_LINE_ESCAPE", 
                  u"HORIZONTAL_WHITESPACE", u"LPAREN", u"RPAREN", u"LBRACK", 
                  u"RBRACK", u"LT", u"GT", u"LBRACE", u"RBRACE", u"MULTI_LINE_COMMENT", 
                  u"COMMENT", u"PASS", u"INCLUDE", u"CONFIG", u"STRING_TYPE", 
                  u"ENUM_TYPE", u"INTEGER_TYPE", u"NUMBER_TYPE", u"BOOLEAN_TYPE", 
                  u"GUID_TYPE", u"DATETIME_TYPE", u"DATE_TYPE", u"TIME_TYPE", 
                  u"DURATION_TYPE", u"FILENAME_TYPE", u"CUSTOM_TYPE", u"STRING_METADATA_VALIDATION", 
                  u"STRING_METADATA_MIN_LENGTH", u"STRING_METADATA_MAX_LENGTH", 
                  u"ENUM_METADATA_VALUES", u"ENUM_METADATA_FRIENDLY_VALUES", 
                  u"METADATA_MIN", u"METADATA_MAX", u"INTEGER_METADATA_BYTES", 
                  u"FILENAME_METADATA_TYPE", u"FILENAME_METADATA_MUST_EXIST", 
                  u"CUSTOM_METADATA_T", u"GENERIC_METADATA_DESCRIPTION", 
                  u"GENERIC_METADATA_PLURAL", u"GENERIC_METADATA_DEFAULT", 
                  u"GENERIC_METADATA_POLYMORPHIC", u"GENERIC_METADATA_SUPPRESS_POLYMORPHIC", 
                  u"SCOPE_DELIMITER", u"ASSIGNMENT", u"COMMA", u"INT", u"NUMBER", 
                  u"ID", u"ARITY_OPTIONAL", u"ARITY_ZERO_OR_MORE", u"ARITY_ONE_OR_MORE", 
                  u"HWS", u"DOUBLE_QUOTE_NUMBER", u"SINGLE_QUOTE_NUMBER", 
                  u"NUMBER_VALUES", u"DOUBLE_QUOTE_INT", u"SINGLE_QUOTE_INT", 
                  u"INT_VALUES", u"DOUBLE_QUOTE_BOOL", u"SINGLE_QUOTE_BOOL", 
                  u"BOOL_VALUES", u"DOUBLE_QUOTE_FILENAME_TYPE", u"SINGLE_QUOTE_FILENAME_TYPE", 
                  u"FILENAME_TYPE_VALUES", u"DOUBLE_QUOTE_STRING", u"SINGLE_QUOTE_STRING", 
                  u"TRIPLE_DOUBLE_QUOTE_STRING", u"TRIPLE_SINGLE_QUOTE_STRING" ]

    grammarFileName = u"SimpleSchema.g4"

    def __init__(self, input=None):
        super(SimpleSchemaLexer, self).__init__(input)
        self.checkVersion("4.5.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None



    multiline_statement_ctr = 0

    def nextToken(self):
        if not hasattr(self, "_denter"):
            self._denter = DenterHelper( super(SimpleSchemaLexer, self).nextToken,
                                         SimpleSchemaParser.NEWLINE,
                                         SimpleSchemaParser.INDENT,
                                         SimpleSchemaParser.DEDENT,
                                       )

        return self._denter.nextToken()



    def action(self, localctx, ruleIndex, actionIndex):
    	if self._actions is None:
    		actions = dict()
    		actions[4] = self.LPAREN_action 
    		actions[5] = self.RPAREN_action 
    		actions[6] = self.LBRACK_action 
    		actions[7] = self.RBRACK_action 
    		actions[8] = self.LT_action 
    		actions[9] = self.GT_action 
    		self._actions = actions
    	action = self._actions.get(ruleIndex, None)
    	if action is not None:
    		action(localctx, actionIndex)
    	else:
    		raise Exception("No registered action for:" + str(ruleIndex))

    def LPAREN_action(self, localctx , actionIndex):
        if actionIndex == 0:
             SimpleSchemaLexer.multiline_statement_ctr += 1 
     

    def RPAREN_action(self, localctx , actionIndex):
        if actionIndex == 1:
             SimpleSchemaLexer.multiline_statement_ctr -= 1 
     

    def LBRACK_action(self, localctx , actionIndex):
        if actionIndex == 2:
             SimpleSchemaLexer.multiline_statement_ctr += 1 
     

    def RBRACK_action(self, localctx , actionIndex):
        if actionIndex == 3:
             SimpleSchemaLexer.multiline_statement_ctr -= 1 
     

    def LT_action(self, localctx , actionIndex):
        if actionIndex == 4:
             SimpleSchemaLexer.multiline_statement_ctr += 1 
     

    def GT_action(self, localctx , actionIndex):
        if actionIndex == 5:
             SimpleSchemaLexer.multiline_statement_ctr -= 1 
     

    def sempred(self, localctx, ruleIndex, predIndex):
        if self._predicates is None:
            preds = dict()
            preds[0] = self.MULTI_LINE_NEWLINE_sempred
            preds[1] = self.NEWLINE_sempred
            self._predicates = preds
        pred = self._predicates.get(ruleIndex, None)
        if pred is not None:
            return pred(localctx, predIndex)
        else:
            raise Exception("No registered predicate for:" + str(ruleIndex))

    def MULTI_LINE_NEWLINE_sempred(self, localctx, predIndex):
            if predIndex == 0:
                return  SimpleSchemaLexer.multiline_statement_ctr != 0 
         

    def NEWLINE_sempred(self, localctx, predIndex):
            if predIndex == 1:
                return  SimpleSchemaLexer.multiline_statement_ctr == 0 
         


