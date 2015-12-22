# Generated from C:\Code\v2\Common\Environment\src\SimpleSchemaCodeGenerator\Grammars\BuildEnvironment\..\Selector.g4 by ANTLR 4.5.1
# encoding: utf-8
from __future__ import print_function
from antlr4 import *
from io import StringIO



from CommonEnvironment.Antlr4Helpers.DenterHelper import DenterHelper
from SelectorParser import SelectorParser



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\2")
        buf.write(u"\65\u01d2\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4")
        buf.write(u",\t,\4-\t-\4.\t.\4/\t/\4\60\t\60\4\61\t\61\4\62\t\62")
        buf.write(u"\4\63\t\63\4\64\t\64\3\2\3\2\5\2l\n\2\3\2\3\2\3\2\3\2")
        buf.write(u"\3\3\3\3\5\3t\n\3\3\3\3\3\7\3x\n\3\f\3\16\3{\13\3\3\4")
        buf.write(u"\3\4\5\4\177\n\4\3\4\3\4\3\4\3\4\3\5\6\5\u0086\n\5\r")
        buf.write(u"\5\16\5\u0087\3\5\3\5\3\6\3\6\3\6\3\6\7\6\u0090\n\6\f")
        buf.write(u"\6\16\6\u0093\13\6\3\6\3\6\3\6\3\6\3\6\3\7\3\7\7\7\u009c")
        buf.write(u"\n\7\f\7\16\7\u009f\13\7\3\7\3\7\3\b\3\b\3\t\3\t\3\n")
        buf.write(u"\3\n\3\13\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3")
        buf.write(u"\20\3\20\3\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25")
        buf.write(u"\3\25\3\26\5\26\u00c0\n\26\3\26\6\26\u00c3\n\26\r\26")
        buf.write(u"\16\26\u00c4\3\27\3\27\7\27\u00c9\n\27\f\27\16\27\u00cc")
        buf.write(u"\13\27\3\30\3\30\3\30\3\30\3\30\3\31\3\31\3\31\3\31\3")
        buf.write(u"\31\3\31\3\31\3\32\3\32\3\32\3\32\3\32\3\32\3\32\3\33")
        buf.write(u"\3\33\3\33\3\33\3\33\3\33\3\33\3\33\3\33\3\34\3\34\3")
        buf.write(u"\34\3\34\3\34\3\34\3\34\3\34\3\34\3\34\3\34\3\34\3\35")
        buf.write(u"\3\35\3\35\3\35\3\35\3\35\3\35\3\36\3\36\3\36\3\36\3")
        buf.write(u"\36\3\37\3\37\3\37\3\37\3\37\3\37\3\37\3\37\3 \3 \3 ")
        buf.write(u"\3 \3 \3 \3 \3!\3!\3!\3!\3!\3!\3!\3!\3\"\3\"\3\"\3\"")
        buf.write(u"\3\"\3#\3#\3#\3#\3#\3#\3#\3#\3#\3$\3$\3$\3$\3$\3%\3%")
        buf.write(u"\3%\3%\3%\3&\3&\3&\3&\3&\3&\3&\3&\3&\3\'\3\'\3\'\3\'")
        buf.write(u"\3\'\3\'\3\'\3\'\3\'\3(\3(\3(\3(\3(\3(\3(\3)\3)\3)\3")
        buf.write(u")\3*\3*\3*\3*\3*\3+\3+\3+\3+\3+\3+\3+\3,\3,\3,\3,\3,")
        buf.write(u"\3-\3-\3-\3-\3-\3-\3-\3-\3-\3-\3.\3.\3.\3.\3.\3.\3.\3")
        buf.write(u".\3.\3.\3.\3.\3.\3.\3.\3.\3.\3.\3.\3/\3/\3/\3/\3/\3/")
        buf.write(u"\3/\3/\3/\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60")
        buf.write(u"\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\61\3")
        buf.write(u"\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61")
        buf.write(u"\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3")
        buf.write(u"\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62")
        buf.write(u"\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\64\3")
        buf.write(u"\64\3\64\3\64\3\64\3\64\3\64\3\64\3\64\3\64\3\64\3\64")
        buf.write(u"\3\64\3\64\3\64\3\64\3\64\3\64\3\u0091\2\65\3\3\5\4\7")
        buf.write(u"\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27\r\31\16\33\17")
        buf.write(u"\35\20\37\21!\22#\23%\24\'\25)\26+\27-\30/\31\61\32\63")
        buf.write(u"\33\65\34\67\359\36;\37= ?!A\"C#E$G%I&K\'M(O)Q*S+U,W")
        buf.write(u"-Y.[/]\60_\61a\62c\63e\64g\65\3\2\7\4\2\13\13\"\"\4\2")
        buf.write(u"\f\f\17\17\3\2\62;\5\2C\\aac|\7\2/\60\62;C\\aac|\u01db")
        buf.write(u"\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13")
        buf.write(u"\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3")
        buf.write(u"\2\2\2\2\25\3\2\2\2\2\27\3\2\2\2\2\31\3\2\2\2\2\33\3")
        buf.write(u"\2\2\2\2\35\3\2\2\2\2\37\3\2\2\2\2!\3\2\2\2\2#\3\2\2")
        buf.write(u"\2\2%\3\2\2\2\2\'\3\2\2\2\2)\3\2\2\2\2+\3\2\2\2\2-\3")
        buf.write(u"\2\2\2\2/\3\2\2\2\2\61\3\2\2\2\2\63\3\2\2\2\2\65\3\2")
        buf.write(u"\2\2\2\67\3\2\2\2\29\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2\2")
        buf.write(u"?\3\2\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2")
        buf.write(u"\2I\3\2\2\2\2K\3\2\2\2\2M\3\2\2\2\2O\3\2\2\2\2Q\3\2\2")
        buf.write(u"\2\2S\3\2\2\2\2U\3\2\2\2\2W\3\2\2\2\2Y\3\2\2\2\2[\3\2")
        buf.write(u"\2\2\2]\3\2\2\2\2_\3\2\2\2\2a\3\2\2\2\2c\3\2\2\2\2e\3")
        buf.write(u"\2\2\2\2g\3\2\2\2\3i\3\2\2\2\5q\3\2\2\2\7|\3\2\2\2\t")
        buf.write(u"\u0085\3\2\2\2\13\u008b\3\2\2\2\r\u0099\3\2\2\2\17\u00a2")
        buf.write(u"\3\2\2\2\21\u00a4\3\2\2\2\23\u00a6\3\2\2\2\25\u00a8\3")
        buf.write(u"\2\2\2\27\u00aa\3\2\2\2\31\u00ac\3\2\2\2\33\u00ae\3\2")
        buf.write(u"\2\2\35\u00b0\3\2\2\2\37\u00b2\3\2\2\2!\u00b4\3\2\2\2")
        buf.write(u"#\u00b6\3\2\2\2%\u00b8\3\2\2\2\'\u00ba\3\2\2\2)\u00bc")
        buf.write(u"\3\2\2\2+\u00bf\3\2\2\2-\u00c6\3\2\2\2/\u00cd\3\2\2\2")
        buf.write(u"\61\u00d2\3\2\2\2\63\u00d9\3\2\2\2\65\u00e0\3\2\2\2\67")
        buf.write(u"\u00e9\3\2\2\29\u00f5\3\2\2\2;\u00fc\3\2\2\2=\u0101\3")
        buf.write(u"\2\2\2?\u0109\3\2\2\2A\u0110\3\2\2\2C\u0118\3\2\2\2E")
        buf.write(u"\u011d\3\2\2\2G\u0126\3\2\2\2I\u012b\3\2\2\2K\u0130\3")
        buf.write(u"\2\2\2M\u0139\3\2\2\2O\u0142\3\2\2\2Q\u0149\3\2\2\2S")
        buf.write(u"\u014d\3\2\2\2U\u0152\3\2\2\2W\u0159\3\2\2\2Y\u015e\3")
        buf.write(u"\2\2\2[\u0168\3\2\2\2]\u017b\3\2\2\2_\u0184\3\2\2\2a")
        buf.write(u"\u0196\3\2\2\2c\u01a2\3\2\2\2e\u01b7\3\2\2\2g\u01c0\3")
        buf.write(u"\2\2\2ik\6\2\2\2jl\7\17\2\2kj\3\2\2\2kl\3\2\2\2lm\3\2")
        buf.write(u"\2\2mn\7\f\2\2no\3\2\2\2op\b\2\2\2p\4\3\2\2\2qs\6\3\3")
        buf.write(u"\2rt\7\17\2\2sr\3\2\2\2st\3\2\2\2tu\3\2\2\2uy\7\f\2\2")
        buf.write(u"vx\t\2\2\2wv\3\2\2\2x{\3\2\2\2yw\3\2\2\2yz\3\2\2\2z\6")
        buf.write(u"\3\2\2\2{y\3\2\2\2|~\7^\2\2}\177\7\17\2\2~}\3\2\2\2~")
        buf.write(u"\177\3\2\2\2\177\u0080\3\2\2\2\u0080\u0081\7\f\2\2\u0081")
        buf.write(u"\u0082\3\2\2\2\u0082\u0083\b\4\2\2\u0083\b\3\2\2\2\u0084")
        buf.write(u"\u0086\t\2\2\2\u0085\u0084\3\2\2\2\u0086\u0087\3\2\2")
        buf.write(u"\2\u0087\u0085\3\2\2\2\u0087\u0088\3\2\2\2\u0088\u0089")
        buf.write(u"\3\2\2\2\u0089\u008a\b\5\2\2\u008a\n\3\2\2\2\u008b\u008c")
        buf.write(u"\7%\2\2\u008c\u008d\7\61\2\2\u008d\u0091\3\2\2\2\u008e")
        buf.write(u"\u0090\13\2\2\2\u008f\u008e\3\2\2\2\u0090\u0093\3\2\2")
        buf.write(u"\2\u0091\u0092\3\2\2\2\u0091\u008f\3\2\2\2\u0092\u0094")
        buf.write(u"\3\2\2\2\u0093\u0091\3\2\2\2\u0094\u0095\7\61\2\2\u0095")
        buf.write(u"\u0096\7%\2\2\u0096\u0097\3\2\2\2\u0097\u0098\b\6\2\2")
        buf.write(u"\u0098\f\3\2\2\2\u0099\u009d\7%\2\2\u009a\u009c\n\3\2")
        buf.write(u"\2\u009b\u009a\3\2\2\2\u009c\u009f\3\2\2\2\u009d\u009b")
        buf.write(u"\3\2\2\2\u009d\u009e\3\2\2\2\u009e\u00a0\3\2\2\2\u009f")
        buf.write(u"\u009d\3\2\2\2\u00a0\u00a1\b\7\2\2\u00a1\16\3\2\2\2\u00a2")
        buf.write(u"\u00a3\7<\2\2\u00a3\20\3\2\2\2\u00a4\u00a5\7\61\2\2\u00a5")
        buf.write(u"\22\3\2\2\2\u00a6\u00a7\7-\2\2\u00a7\24\3\2\2\2\u00a8")
        buf.write(u"\u00a9\7,\2\2\u00a9\26\3\2\2\2\u00aa\u00ab\7\60\2\2\u00ab")
        buf.write(u"\30\3\2\2\2\u00ac\u00ad\7>\2\2\u00ad\32\3\2\2\2\u00ae")
        buf.write(u"\u00af\7@\2\2\u00af\34\3\2\2\2\u00b0\u00b1\7]\2\2\u00b1")
        buf.write(u"\36\3\2\2\2\u00b2\u00b3\7_\2\2\u00b3 \3\2\2\2\u00b4\u00b5")
        buf.write(u"\7*\2\2\u00b5\"\3\2\2\2\u00b6\u00b7\7+\2\2\u00b7$\3\2")
        buf.write(u"\2\2\u00b8\u00b9\7}\2\2\u00b9&\3\2\2\2\u00ba\u00bb\7")
        buf.write(u"\177\2\2\u00bb(\3\2\2\2\u00bc\u00bd\7.\2\2\u00bd*\3\2")
        buf.write(u"\2\2\u00be\u00c0\7/\2\2\u00bf\u00be\3\2\2\2\u00bf\u00c0")
        buf.write(u"\3\2\2\2\u00c0\u00c2\3\2\2\2\u00c1\u00c3\t\4\2\2\u00c2")
        buf.write(u"\u00c1\3\2\2\2\u00c3\u00c4\3\2\2\2\u00c4\u00c2\3\2\2")
        buf.write(u"\2\u00c4\u00c5\3\2\2\2\u00c5,\3\2\2\2\u00c6\u00ca\t\5")
        buf.write(u"\2\2\u00c7\u00c9\t\6\2\2\u00c8\u00c7\3\2\2\2\u00c9\u00cc")
        buf.write(u"\3\2\2\2\u00ca\u00c8\3\2\2\2\u00ca\u00cb\3\2\2\2\u00cb")
        buf.write(u".\3\2\2\2\u00cc\u00ca\3\2\2\2\u00cd\u00ce\7r\2\2\u00ce")
        buf.write(u"\u00cf\7c\2\2\u00cf\u00d0\7u\2\2\u00d0\u00d1\7u\2\2\u00d1")
        buf.write(u"\60\3\2\2\2\u00d2\u00d3\7q\2\2\u00d3\u00d4\7d\2\2\u00d4")
        buf.write(u"\u00d5\7l\2\2\u00d5\u00d6\7g\2\2\u00d6\u00d7\7e\2\2\u00d7")
        buf.write(u"\u00d8\7v\2\2\u00d8\62\3\2\2\2\u00d9\u00da\7u\2\2\u00da")
        buf.write(u"\u00db\7k\2\2\u00db\u00dc\7o\2\2\u00dc\u00dd\7r\2\2\u00dd")
        buf.write(u"\u00de\7n\2\2\u00de\u00df\7g\2\2\u00df\64\3\2\2\2\u00e0")
        buf.write(u"\u00e1\7e\2\2\u00e1\u00e2\7q\2\2\u00e2\u00e3\7o\2\2\u00e3")
        buf.write(u"\u00e4\7r\2\2\u00e4\u00e5\7q\2\2\u00e5\u00e6\7w\2\2\u00e6")
        buf.write(u"\u00e7\7p\2\2\u00e7\u00e8\7f\2\2\u00e8\66\3\2\2\2\u00e9")
        buf.write(u"\u00ea\7h\2\2\u00ea\u00eb\7w\2\2\u00eb\u00ec\7p\2\2\u00ec")
        buf.write(u"\u00ed\7f\2\2\u00ed\u00ee\7c\2\2\u00ee\u00ef\7o\2\2\u00ef")
        buf.write(u"\u00f0\7g\2\2\u00f0\u00f1\7p\2\2\u00f1\u00f2\7v\2\2\u00f2")
        buf.write(u"\u00f3\7c\2\2\u00f3\u00f4\7n\2\2\u00f48\3\2\2\2\u00f5")
        buf.write(u"\u00f6\7u\2\2\u00f6\u00f7\7v\2\2\u00f7\u00f8\7t\2\2\u00f8")
        buf.write(u"\u00f9\7k\2\2\u00f9\u00fa\7p\2\2\u00fa\u00fb\7i\2\2\u00fb")
        buf.write(u":\3\2\2\2\u00fc\u00fd\7g\2\2\u00fd\u00fe\7p\2\2\u00fe")
        buf.write(u"\u00ff\7w\2\2\u00ff\u0100\7o\2\2\u0100<\3\2\2\2\u0101")
        buf.write(u"\u0102\7k\2\2\u0102\u0103\7p\2\2\u0103\u0104\7v\2\2\u0104")
        buf.write(u"\u0105\7g\2\2\u0105\u0106\7i\2\2\u0106\u0107\7g\2\2\u0107")
        buf.write(u"\u0108\7t\2\2\u0108>\3\2\2\2\u0109\u010a\7p\2\2\u010a")
        buf.write(u"\u010b\7w\2\2\u010b\u010c\7o\2\2\u010c\u010d\7d\2\2\u010d")
        buf.write(u"\u010e\7g\2\2\u010e\u010f\7t\2\2\u010f@\3\2\2\2\u0110")
        buf.write(u"\u0111\7d\2\2\u0111\u0112\7q\2\2\u0112\u0113\7q\2\2\u0113")
        buf.write(u"\u0114\7n\2\2\u0114\u0115\7g\2\2\u0115\u0116\7c\2\2\u0116")
        buf.write(u"\u0117\7p\2\2\u0117B\3\2\2\2\u0118\u0119\7i\2\2\u0119")
        buf.write(u"\u011a\7w\2\2\u011a\u011b\7k\2\2\u011b\u011c\7f\2\2\u011c")
        buf.write(u"D\3\2\2\2\u011d\u011e\7f\2\2\u011e\u011f\7c\2\2\u011f")
        buf.write(u"\u0120\7v\2\2\u0120\u0121\7g\2\2\u0121\u0122\7v\2\2\u0122")
        buf.write(u"\u0123\7k\2\2\u0123\u0124\7o\2\2\u0124\u0125\7g\2\2\u0125")
        buf.write(u"F\3\2\2\2\u0126\u0127\7f\2\2\u0127\u0128\7c\2\2\u0128")
        buf.write(u"\u0129\7v\2\2\u0129\u012a\7g\2\2\u012aH\3\2\2\2\u012b")
        buf.write(u"\u012c\7v\2\2\u012c\u012d\7k\2\2\u012d\u012e\7o\2\2\u012e")
        buf.write(u"\u012f\7g\2\2\u012fJ\3\2\2\2\u0130\u0131\7f\2\2\u0131")
        buf.write(u"\u0132\7w\2\2\u0132\u0133\7t\2\2\u0133\u0134\7c\2\2\u0134")
        buf.write(u"\u0135\7v\2\2\u0135\u0136\7k\2\2\u0136\u0137\7q\2\2\u0137")
        buf.write(u"\u0138\7p\2\2\u0138L\3\2\2\2\u0139\u013a\7h\2\2\u013a")
        buf.write(u"\u013b\7k\2\2\u013b\u013c\7n\2\2\u013c\u013d\7g\2\2\u013d")
        buf.write(u"\u013e\7p\2\2\u013e\u013f\7c\2\2\u013f\u0140\7o\2\2\u0140")
        buf.write(u"\u0141\7g\2\2\u0141N\3\2\2\2\u0142\u0143\7e\2\2\u0143")
        buf.write(u"\u0144\7w\2\2\u0144\u0145\7u\2\2\u0145\u0146\7v\2\2\u0146")
        buf.write(u"\u0147\7q\2\2\u0147\u0148\7o\2\2\u0148P\3\2\2\2\u0149")
        buf.write(u"\u014a\7r\2\2\u014a\u014b\7t\2\2\u014b\u014c\7g\2\2\u014c")
        buf.write(u"R\3\2\2\2\u014d\u014e\7r\2\2\u014e\u014f\7q\2\2\u014f")
        buf.write(u"\u0150\7u\2\2\u0150\u0151\7v\2\2\u0151T\3\2\2\2\u0152")
        buf.write(u"\u0153\7k\2\2\u0153\u0154\7p\2\2\u0154\u0155\7n\2\2\u0155")
        buf.write(u"\u0156\7k\2\2\u0156\u0157\7p\2\2\u0157\u0158\7g\2\2\u0158")
        buf.write(u"V\3\2\2\2\u0159\u015a\7u\2\2\u015a\u015b\7g\2\2\u015b")
        buf.write(u"\u015c\7n\2\2\u015c\u015d\7h\2\2\u015dX\3\2\2\2\u015e")
        buf.write(u"\u015f\7c\2\2\u015f\u0160\7p\2\2\u0160\u0161\7e\2\2\u0161")
        buf.write(u"\u0162\7g\2\2\u0162\u0163\7u\2\2\u0163\u0164\7v\2\2\u0164")
        buf.write(u"\u0165\7q\2\2\u0165\u0166\7t\2\2\u0166\u0167\7u\2\2\u0167")
        buf.write(u"Z\3\2\2\2\u0168\u0169\7c\2\2\u0169\u016a\7p\2\2\u016a")
        buf.write(u"\u016b\7e\2\2\u016b\u016c\7g\2\2\u016c\u016d\7u\2\2\u016d")
        buf.write(u"\u016e\7v\2\2\u016e\u016f\7q\2\2\u016f\u0170\7t\2\2\u0170")
        buf.write(u"\u0171\7u\2\2\u0171\u0172\7a\2\2\u0172\u0173\7c\2\2\u0173")
        buf.write(u"\u0174\7p\2\2\u0174\u0175\7f\2\2\u0175\u0176\7a\2\2\u0176")
        buf.write(u"\u0177\7u\2\2\u0177\u0178\7g\2\2\u0178\u0179\7n\2\2\u0179")
        buf.write(u"\u017a\7h\2\2\u017a\\\3\2\2\2\u017b\u017c\7e\2\2\u017c")
        buf.write(u"\u017d\7j\2\2\u017d\u017e\7k\2\2\u017e\u017f\7n\2\2\u017f")
        buf.write(u"\u0180\7f\2\2\u0180\u0181\7t\2\2\u0181\u0182\7g\2\2\u0182")
        buf.write(u"\u0183\7p\2\2\u0183^\3\2\2\2\u0184\u0185\7u\2\2\u0185")
        buf.write(u"\u0186\7g\2\2\u0186\u0187\7n\2\2\u0187\u0188\7h\2\2\u0188")
        buf.write(u"\u0189\7a\2\2\u0189\u018a\7c\2\2\u018a\u018b\7p\2\2\u018b")
        buf.write(u"\u018c\7f\2\2\u018c\u018d\7a\2\2\u018d\u018e\7e\2\2\u018e")
        buf.write(u"\u018f\7j\2\2\u018f\u0190\7k\2\2\u0190\u0191\7n\2\2\u0191")
        buf.write(u"\u0192\7f\2\2\u0192\u0193\7t\2\2\u0193\u0194\7g\2\2\u0194")
        buf.write(u"\u0195\7p\2\2\u0195`\3\2\2\2\u0196\u0197\7f\2\2\u0197")
        buf.write(u"\u0198\7g\2\2\u0198\u0199\7u\2\2\u0199\u019a\7e\2\2\u019a")
        buf.write(u"\u019b\7g\2\2\u019b\u019c\7p\2\2\u019c\u019d\7f\2\2\u019d")
        buf.write(u"\u019e\7c\2\2\u019e\u019f\7p\2\2\u019f\u01a0\7v\2\2\u01a0")
        buf.write(u"\u01a1\7u\2\2\u01a1b\3\2\2\2\u01a2\u01a3\7u\2\2\u01a3")
        buf.write(u"\u01a4\7g\2\2\u01a4\u01a5\7n\2\2\u01a5\u01a6\7h\2\2\u01a6")
        buf.write(u"\u01a7\7a\2\2\u01a7\u01a8\7c\2\2\u01a8\u01a9\7p\2\2\u01a9")
        buf.write(u"\u01aa\7f\2\2\u01aa\u01ab\7a\2\2\u01ab\u01ac\7f\2\2\u01ac")
        buf.write(u"\u01ad\7g\2\2\u01ad\u01ae\7u\2\2\u01ae\u01af\7e\2\2\u01af")
        buf.write(u"\u01b0\7g\2\2\u01b0\u01b1\7p\2\2\u01b1\u01b2\7f\2\2\u01b2")
        buf.write(u"\u01b3\7c\2\2\u01b3\u01b4\7p\2\2\u01b4\u01b5\7v\2\2\u01b5")
        buf.write(u"\u01b6\7u\2\2\u01b6d\3\2\2\2\u01b7\u01b8\7u\2\2\u01b8")
        buf.write(u"\u01b9\7k\2\2\u01b9\u01ba\7d\2\2\u01ba\u01bb\7n\2\2\u01bb")
        buf.write(u"\u01bc\7k\2\2\u01bc\u01bd\7p\2\2\u01bd\u01be\7i\2\2\u01be")
        buf.write(u"\u01bf\7u\2\2\u01bff\3\2\2\2\u01c0\u01c1\7u\2\2\u01c1")
        buf.write(u"\u01c2\7g\2\2\u01c2\u01c3\7n\2\2\u01c3\u01c4\7h\2\2\u01c4")
        buf.write(u"\u01c5\7a\2\2\u01c5\u01c6\7c\2\2\u01c6\u01c7\7p\2\2\u01c7")
        buf.write(u"\u01c8\7f\2\2\u01c8\u01c9\7a\2\2\u01c9\u01ca\7u\2\2\u01ca")
        buf.write(u"\u01cb\7k\2\2\u01cb\u01cc\7d\2\2\u01cc\u01cd\7n\2\2\u01cd")
        buf.write(u"\u01ce\7k\2\2\u01ce\u01cf\7p\2\2\u01cf\u01d0\7i\2\2\u01d0")
        buf.write(u"\u01d1\7u\2\2\u01d1h\3\2\2\2\r\2ksy~\u0087\u0091\u009d")
        buf.write(u"\u00bf\u00c4\u00ca\3\b\2\2")
        return buf.getvalue()


class SelectorLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]


    MULTI_LINE_NEWLINE = 1
    NEWLINE = 2
    MULTI_LINE_ESCAPE = 3
    HORIZONTAL_WHITESPACE = 4
    MULTI_LINE_COMMENT = 5
    COMMENT = 6
    SCOPE_DELIMITER = 7
    SEP = 8
    ONE_OR_MORE = 9
    ZERO_OR_MORE = 10
    ANY = 11
    LT = 12
    GT = 13
    LBRACK = 14
    RBRACK = 15
    LPAREN = 16
    RPAREN = 17
    LBRACE = 18
    RBRACE = 19
    COMMA = 20
    INT = 21
    ID = 22
    PASS = 23
    PREDICATE_OBJECT = 24
    PREDICATE_SIMPLE_OBJECT = 25
    PREDICATE_COMPOUND_OBJECT = 26
    PREDICATE_FUNDAMENTAL = 27
    PREDICATE_STRING = 28
    PREDICATE_ENUM = 29
    PREDICATE_INTEGER = 30
    PREDICATE_NUMBER = 31
    PREDICATE_BOOLEAN = 32
    PREDICATE_GUID = 33
    PREDICATE_DATETIME = 34
    PREDICATE_DATE = 35
    PREDICATE_TIME = 36
    PREDICATE_DURATION = 37
    PREDICATE_FILENAME = 38
    PREDICATE_CUSTOM = 39
    CALL_TYPE_PRE = 40
    CALL_TYPE_POST = 41
    CALL_TYPE_INLINE = 42
    DECORATOR_SELF = 43
    DECORATOR_ANCESTORS = 44
    DECORATOR_ANCESTORS_AND_SELF = 45
    DECORATOR_CHILDREN = 46
    DECORATOR_SELF_AND_CHILDREN = 47
    DECORATOR_DESCENDANTS = 48
    DECORATOR_SELF_AND_DESCENDANTS = 49
    DECORATOR_SIBLINGS = 50
    DECORATOR_SELF_AND_SIBLINGS = 51

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"':'", u"'/'", u"'+'", u"'*'", u"'.'", u"'<'", u"'>'", u"'['", 
            u"']'", u"'('", u"')'", u"'{'", u"'}'", u"','", u"'pass'", u"'object'", 
            u"'simple'", u"'compound'", u"'fundamental'", u"'string'", u"'enum'", 
            u"'integer'", u"'number'", u"'boolean'", u"'guid'", u"'datetime'", 
            u"'date'", u"'time'", u"'duration'", u"'filename'", u"'custom'", 
            u"'pre'", u"'post'", u"'inline'", u"'self'", u"'ancestors'", 
            u"'ancestors_and_self'", u"'children'", u"'self_and_children'", 
            u"'descendants'", u"'self_and_descendants'", u"'siblings'", 
            u"'self_and_siblings'" ]

    symbolicNames = [ u"<INVALID>",
            u"MULTI_LINE_NEWLINE", u"NEWLINE", u"MULTI_LINE_ESCAPE", u"HORIZONTAL_WHITESPACE", 
            u"MULTI_LINE_COMMENT", u"COMMENT", u"SCOPE_DELIMITER", u"SEP", 
            u"ONE_OR_MORE", u"ZERO_OR_MORE", u"ANY", u"LT", u"GT", u"LBRACK", 
            u"RBRACK", u"LPAREN", u"RPAREN", u"LBRACE", u"RBRACE", u"COMMA", 
            u"INT", u"ID", u"PASS", u"PREDICATE_OBJECT", u"PREDICATE_SIMPLE_OBJECT", 
            u"PREDICATE_COMPOUND_OBJECT", u"PREDICATE_FUNDAMENTAL", u"PREDICATE_STRING", 
            u"PREDICATE_ENUM", u"PREDICATE_INTEGER", u"PREDICATE_NUMBER", 
            u"PREDICATE_BOOLEAN", u"PREDICATE_GUID", u"PREDICATE_DATETIME", 
            u"PREDICATE_DATE", u"PREDICATE_TIME", u"PREDICATE_DURATION", 
            u"PREDICATE_FILENAME", u"PREDICATE_CUSTOM", u"CALL_TYPE_PRE", 
            u"CALL_TYPE_POST", u"CALL_TYPE_INLINE", u"DECORATOR_SELF", u"DECORATOR_ANCESTORS", 
            u"DECORATOR_ANCESTORS_AND_SELF", u"DECORATOR_CHILDREN", u"DECORATOR_SELF_AND_CHILDREN", 
            u"DECORATOR_DESCENDANTS", u"DECORATOR_SELF_AND_DESCENDANTS", 
            u"DECORATOR_SIBLINGS", u"DECORATOR_SELF_AND_SIBLINGS" ]

    ruleNames = [ u"MULTI_LINE_NEWLINE", u"NEWLINE", u"MULTI_LINE_ESCAPE", 
                  u"HORIZONTAL_WHITESPACE", u"MULTI_LINE_COMMENT", u"COMMENT", 
                  u"SCOPE_DELIMITER", u"SEP", u"ONE_OR_MORE", u"ZERO_OR_MORE", 
                  u"ANY", u"LT", u"GT", u"LBRACK", u"RBRACK", u"LPAREN", 
                  u"RPAREN", u"LBRACE", u"RBRACE", u"COMMA", u"INT", u"ID", 
                  u"PASS", u"PREDICATE_OBJECT", u"PREDICATE_SIMPLE_OBJECT", 
                  u"PREDICATE_COMPOUND_OBJECT", u"PREDICATE_FUNDAMENTAL", 
                  u"PREDICATE_STRING", u"PREDICATE_ENUM", u"PREDICATE_INTEGER", 
                  u"PREDICATE_NUMBER", u"PREDICATE_BOOLEAN", u"PREDICATE_GUID", 
                  u"PREDICATE_DATETIME", u"PREDICATE_DATE", u"PREDICATE_TIME", 
                  u"PREDICATE_DURATION", u"PREDICATE_FILENAME", u"PREDICATE_CUSTOM", 
                  u"CALL_TYPE_PRE", u"CALL_TYPE_POST", u"CALL_TYPE_INLINE", 
                  u"DECORATOR_SELF", u"DECORATOR_ANCESTORS", u"DECORATOR_ANCESTORS_AND_SELF", 
                  u"DECORATOR_CHILDREN", u"DECORATOR_SELF_AND_CHILDREN", 
                  u"DECORATOR_DESCENDANTS", u"DECORATOR_SELF_AND_DESCENDANTS", 
                  u"DECORATOR_SIBLINGS", u"DECORATOR_SELF_AND_SIBLINGS" ]

    grammarFileName = u"Selector.g4"

    def __init__(self, input=None):
        super(SelectorLexer, self).__init__(input)
        self.checkVersion("4.5.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None



    multiline_statement_ctr = 0

    def nextToken(self):
        if not hasattr(self, "_denter"):
            self._denter = DenterHelper( super(SelectorLexer, self).nextToken,
                                         SelectorParser.NEWLINE,
                                         SelectorParser.INDENT,
                                         SelectorParser.DEDENT,
                                       )

        return self._denter.nextToken()



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
                return  SelectorLexer.multiline_statement_ctr != 0 
         

    def NEWLINE_sempred(self, localctx, predIndex):
            if predIndex == 1:
                return  SelectorLexer.multiline_statement_ctr == 0 
         


