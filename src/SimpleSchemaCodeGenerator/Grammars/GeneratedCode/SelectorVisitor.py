# Generated from C:\Code\v2\Common\Environment\src\SimpleSchemaCodeGenerator\Grammars\BuildEnvironment\..\Selector.g4 by ANTLR 4.5.1
from antlr4 import *

# This class defines a complete generic visitor for a parse tree produced by SelectorParser.

class SelectorVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SelectorParser#statements.
    def visitStatements(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#statement___.
    def visitStatement___(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#single_statement.
    def visitSingle_statement(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#compound_statement.
    def visitCompound_statement(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector.
    def visitSelector(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_item.
    def visitSelector_item(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_predicate.
    def visitSelector_predicate(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#call_type___.
    def visitCall_type___(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#call_type_type.
    def visitCall_type_type(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#decorator.
    def visitDecorator(self, ctx):
        return self.visitChildren(ctx)


