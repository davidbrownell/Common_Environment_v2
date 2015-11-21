# Generated from C:\Code\v2\Common\Environment\Libraries\Python\CommonEnvironment\v1.0\CommonEnvironment\SimpleSchema\BuildEnvironment\..\SimpleSchema.g4 by ANTLR 4.5.1
from antlr4 import *

# This class defines a complete generic visitor for a parse tree produced by SimpleSchemaParser.

class SimpleSchemaVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SimpleSchemaParser#numberString.
    def visitNumberString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#intString.
    def visitIntString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#boolString.
    def visitBoolString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#filenameTypeString.
    def visitFilenameTypeString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#string.
    def visitString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enhancedString.
    def visitEnhancedString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arg.
    def visitArg(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#listArg.
    def visitListArg(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#statements.
    def visitStatements(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#headerStatement__.
    def visitHeaderStatement__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#standardStatement__.
    def visitStandardStatement__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#includeStatement__.
    def visitIncludeStatement__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#includeStatement_Name.
    def visitIncludeStatement_Name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#configDeclaration.
    def visitConfigDeclaration(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#configDeclaration_Name.
    def visitConfigDeclaration_Name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#configDeclaration_Content__.
    def visitConfigDeclaration_Content__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#unnamedObj.
    def visitUnnamedObj(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#obj.
    def visitObj(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#obj_Name.
    def visitObj_Name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#obj_Base.
    def visitObj_Base(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#obj_Declaration__.
    def visitObj_Declaration__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#obj_Content__.
    def visitObj_Content__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#unnamedDeclaration.
    def visitUnnamedDeclaration(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration.
    def visitDeclaration(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Name.
    def visitDeclaration_Name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Content__.
    def visitDeclaration_Content__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Type.
    def visitDeclaration_Type(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Metadata__.
    def visitDeclaration_Metadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Metadata_Description.
    def visitDeclaration_Metadata_Description(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Metadata_Plural.
    def visitDeclaration_Metadata_Plural(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Metadata_Polymorphic.
    def visitDeclaration_Metadata_Polymorphic(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration_Metadata_SuppressPolymorphic.
    def visitDeclaration_Metadata_SuppressPolymorphic(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#stringMetadata__.
    def visitStringMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#stringMetadata_Validation.
    def visitStringMetadata_Validation(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#stringMetadata_MaxLength.
    def visitStringMetadata_MaxLength(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#stringMetadata_MinLength.
    def visitStringMetadata_MinLength(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enumValues__.
    def visitEnumValues__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enumValues_Values.
    def visitEnumValues_Values(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enumMetadata__.
    def visitEnumMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enumMetadata_FriendlyValues.
    def visitEnumMetadata_FriendlyValues(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enum_StringList.
    def visitEnum_StringList(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#integerMetadata__.
    def visitIntegerMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#integerMetadata_Bytes.
    def visitIntegerMetadata_Bytes(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#integerMetadata_Max.
    def visitIntegerMetadata_Max(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#integerMetadata_Min.
    def visitIntegerMetadata_Min(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#numberMetadata__.
    def visitNumberMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#numberMetadata_Max.
    def visitNumberMetadata_Max(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#numberMetadata_Min.
    def visitNumberMetadata_Min(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#filenameMetadata__.
    def visitFilenameMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#filenameMetadata_Type.
    def visitFilenameMetadata_Type(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#filenameMetadata_MustExist.
    def visitFilenameMetadata_MustExist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#customMetadata__.
    def visitCustomMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#customMetadata_Type.
    def visitCustomMetadata_Type(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#metadata__.
    def visitMetadata__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#metadata_Name.
    def visitMetadata_Name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity__.
    def visitArity__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity_Optional.
    def visitArity_Optional(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity_ZeroOrMore.
    def visitArity_ZeroOrMore(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity_OneOrMore.
    def visitArity_OneOrMore(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity_Custom.
    def visitArity_Custom(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity_CustomRange.
    def visitArity_CustomRange(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension.
    def visitExtension(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Name.
    def visitExtension_Name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Content__.
    def visitExtension_Content__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Content_Standard__.
    def visitExtension_Content_Standard__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Content_Positional.
    def visitExtension_Content_Positional(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Content_Keywords__.
    def visitExtension_Content_Keywords__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Content_Keyword__.
    def visitExtension_Content_Keyword__(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension_Content_Keyword_Name.
    def visitExtension_Content_Keyword_Name(self, ctx):
        return self.visitChildren(ctx)


