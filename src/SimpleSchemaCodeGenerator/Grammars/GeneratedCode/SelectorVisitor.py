# Generated from C:\Code\v2\Common\Environment\src\SimpleSchemaCodeGenerator\Grammars\BuildEnvironment\..\Selector.g4 by ANTLR 4.5.1
from antlr4 import *

# This class defines a complete generic visitor for a parse tree produced by SelectorParser.

class SelectorVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SelectorParser#arg.
    def visitArg(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#statements.
    def visitStatements(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#statement.
    def visitStatement(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#singleStatement.
    def visitSingleStatement(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#groupStatement.
    def visitGroupStatement(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#function.
    def visitFunction(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector.
    def visitSelector(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_Predicate.
    def visitSelector_Predicate(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_Predicate_Index.
    def visitSelector_Predicate_Index(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_Predicate_IndexRange.
    def visitSelector_Predicate_IndexRange(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_Predicate_Statement.
    def visitSelector_Predicate_Statement(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#selector_Predicate_Statement_Operator.
    def visitSelector_Predicate_Statement_Operator(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SelectorParser#decorator.
    def visitDecorator(self, ctx):
        return self.visitChildren(ctx)


