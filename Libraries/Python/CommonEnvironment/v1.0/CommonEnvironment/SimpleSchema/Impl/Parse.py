# ---------------------------------------------------------------------------
# |  
# |  Parse.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/05/2015 03:10:48 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import itertools
import os
import sys

from collections import OrderedDict
from contextlib import contextmanager

import antlr4

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)   # <Redefining build-in type> pylint: disable = W0622

from ..Exceptions import *
from ..Observer import *

from .Item import *

sys.path.insert(0, os.path.join(_script_dir, "..", "Generated"))
assert os.path.isdir(sys.path[0]), sys.path[0]

with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaLexer import SimpleSchemaLexer                         # <Unable to import> pylint: disable = F0401
    from SimpleSchemaParser import SimpleSchemaParser                       # <Unable to import> pylint: disable = F0401
    from SimpleSchemaVisitor import SimpleSchemaVisitor                     # <Unable to import> pylint: disable = F0401

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def ParseFiles( filenames, 
                observer=None,
              ):
    d = OrderedDict()

    for filename in filenames:
        d[filename] = lambda filename=filename: open(filename).read()

    return ParseEx(d, observer)

# ---------------------------------------------------------------------------
def ParseStrings( named_strings,            # { "<name>" : "<content>", }
                  observer=None,
                ):
    d = OrderedDict()

    # <Unused variable> pylint: disable = W0612
    for k, v in named_strings.iteritems():
        d[k] = lambda v=v: v

    return ParseEx(d, observer)

# ---------------------------------------------------------------------------
def ParseEx( source_name_content_generators,            # { "name" : def Func() -> content, }
             observer=None,
           ):
    observer = observer or DefaultObserver
    include_filenames = []

    root = Item( item_type=Item.Type_Standard,
                 parent=None,
                 source="<root>",
                 line=-1,
                 column=-1,
                 is_external=False,
               )
    root.declaration_type = -SimpleSchemaParser.RULE_obj
    root.config = OrderedDict()

    # ---------------------------------------------------------------------------
    # <Instance of 'Visitor' has no 'visitChildren' member> pylint: disable = E1101
    class Visitor(SimpleSchemaVisitor):
        
        # ---------------------------------------------------------------------------
        def __init__(self, source_name, is_external):
            self._source_name               = source_name
            self._is_external               = is_external

            self._stack                     = [ root, ]

        # ---------------------------------------------------------------------------
        def visitNumberString(self, ctx):
            result = [ None, ]

            # ---------------------------------------------------------------------------
            def Functor(value):
                result[0] = float(value)

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            self.visitEnhancedString(ctx)

            assert callable(self._stack[-1])
            
            result = self._stack[-1](result[0])
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitIntString(self, ctx):
            result = [ None, ]

            # ---------------------------------------------------------------------------
            def Functor(value):
                result[0] = int(value)

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            self.visitEnhancedString(ctx)

            assert callable(self._stack[-1])

            result = self._stack[-1](result[0])
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitBoolString(self, ctx):
            result = [ None, ]

            # ---------------------------------------------------------------------------
            def Functor(value):
                result[0] = value in [ "true", "t", "yes", "y", "1", ]

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            self.visitEnhancedString(ctx)

            assert callable(self._stack[-1])

            result = self._stack[-1](result[0])
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitFilenameTypeString(self, ctx):
            return self.visitEnhancedString(ctx)

        # ---------------------------------------------------------------------------
        def visitString(self, ctx):
            return self.visitEnhancedString(ctx)

        # ---------------------------------------------------------------------------
        def visitEnhancedString(self, ctx):
            while not isinstance(ctx, antlr4.tree.Tree.TerminalNode):
                assert len(ctx.children) == 1
                ctx = ctx.children[0]

            token = ctx.symbol
            value = token.text

            assert len(value) >= 2, value

            if ( (value.startswith('"""') and value.endswith('"""')) or
                 (value.startswith("'''") and value.endswith("'''"))
               ):
                initial_whitespace = token.column

                # ---------------------------------------------------------------------------
                def TrimPrefix(line, line_offset):
                    index = 0
                    whitespace = 0

                    while index < len(line) and whitespace < initial_whitespace:
                        if line[index] == ' ':
                            whitespace += 1
                        elif line[index] == '\t':
                            whitespace += 4
                        elif line[index] == '\r':
                            break
                        else:
                            raise ParseInvalidTripleStringPrefix( self._source_name,
                                                                  token.line + line_offset,
                                                                  token.column + 1 + whitespace,
                                                                )

                        index += 1

                    return line[index:]

                # ---------------------------------------------------------------------------
                
                lines = value.split('\n')

                initial_line = lines[0].rstrip()
                if len(initial_line) != 3:
                    raise ParseInvalidTripleStringHeader( self._source_name,
                                                          token.line,
                                                          token.column + 1,
                                                        )

                final_line = lines[-1]
                if len(TrimPrefix(final_line, len(lines))) != 3:
                    raise ParseInvalidTriplStringFooter( self._source_name,
                                                         token.line,
                                                         token.column + 1,
                                                       )

                lines = [ TrimPrefix(line, index + 1) for index, line in enumerate(lines[1:-1]) ]

                value = '\n'.join(lines)

            elif value[0] == '"' and value[-1] == '"':
                value = value[1:-1].replace('\\"', '"')

            elif value[0] == "'" and value[-1] == "'":
                value = value[1:-1].replace("\\'", "'")

            else:
                assert False, value

            assert callable(self._stack[-1])
            
            result = self._stack[-1](value)
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitArg(self, ctx):
            assert len(ctx.children) == 1
            child = ctx.children[0]

            if isinstance(child, SimpleSchemaParser.EnhancedStringContext):
                value = [ None, ]

                # ---------------------------------------------------------------------------
                def Functor(v):
                    value[0] = '"{}"'.format(v)

                # ---------------------------------------------------------------------------
                
                self._stack.append(Functor)
                self.visitEnhancedString(child)
                
                value = value[0]

            elif isinstance(child, SimpleSchemaParser.ListArgContext):
                value = [ None, ]

                # ---------------------------------------------------------------------------
                def Functor(v):
                    value[0] = v

                # ---------------------------------------------------------------------------
                
                self._stack.append(Functor)
                self.visitListArg(child)

                value = value[0]

            elif child.symbol.type == ctx.parser.ID:
                value = child.symbol.text
            
            elif child.symbol.type == ctx.parser.INT:
                value = int(child.symbol.text)
            
            elif child.symbol.type == ctx.parser.NUMBER:
                value = float(child.symbol.text)
            
            else:
                assert False

            assert callable(self._stack[-1])

            result = self._stack[-1](value)
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitListArg(self, ctx):
            values = []

            # ---------------------------------------------------------------------------
            def Functor(v):
                values.append(v)
                return False

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            with CallOnExit(self._stack.pop):
                self.visitChildren(ctx)

            assert callable(self._stack[-1])

            result = self._stack[-1](values)
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitIncludeStatement_Name(self, ctx):
            # ---------------------------------------------------------------------------
            def Functor(value):
                filename = os.path.normpath(os.path.join(os.path.dirname(self._source_name), value))
                if not os.path.isfile(filename):
                    raise ParseInvalidIncludeException( self._source_name,
                                                        ctx.symbol.line,
                                                        ctx.symbol.column + 1,
                                                        name=filename,
                                                      )

                if ( filename not in source_name_content_generators and
                     filename not in include_filenames
                   ):
                    include_filenames.append(filename)

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)

        # ---------------------------------------------------------------------------
        def visitConfigDeclaration(self, ctx):
            with self._PushNewStackItem(ctx) as item:
                self.visitChildren(ctx)

            if item.name in root.config:
                raise ParseDuplicateConfigException( self._source_name,
                                                     ctx.start.symbol.line,
                                                     ctx.start.symbol.column + 1,
                                                     name=item.name,
                                                     source=root.config[item.name].Source,
                                                     line=root.config[item.name].Line,
                                                     column=root.config[item.name].Column,
                                                   )

            root.config[item.name] = item
            item.subtype = Item.SubType_Config

            # The config item is not associated with the root and needs to be removed
            # from this parent.
            assert self._stack[-1].items[-1] == item
            self._stack[-1].items.pop()

        # ---------------------------------------------------------------------------
        def visitConfigDeclaration_Name(self, ctx):
            obj = self._stack[-1]

            # ---------------------------------------------------------------------------
            def Functor(value):
                obj.name = value

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitUnnamedObj(self, ctx):
            with self._PushNewStackItem(ctx) as item:
                item.declaration_type = -ctx.parser.RULE_obj
                self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitObj(self, ctx):
            with self._PushNewStackItem(ctx) as item:
                item.declaration_type = -ctx.parser.RULE_obj
                self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitObj_Name(self, ctx):
            assert len(ctx.children) == 1
            self._stack[-1].name = ctx.children[0].symbol.text

        # ---------------------------------------------------------------------------
        def visitObj_Base(self, ctx):
            with self._PushNewStackItem(ctx) as item:
                self.visitChildren(ctx)

            # This item isn't a child of the parent, but rather its base
            assert self._stack[-1].items[-1] == item
            self._stack[-1].items.pop()

            self._stack[-1].reference = item

        # ---------------------------------------------------------------------------
        def visitUnnamedDeclaration(self, ctx):
            with self._PushNewStackItem(ctx):
                return self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitDeclaration(self, ctx):
            with self._PushNewStackItem(ctx):
                return self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitDeclaration_Name(self, ctx):
            assert len(ctx.children) == 1
            self._stack[-1].name = ctx.children[0].symbol.text

        # ---------------------------------------------------------------------------
        def visitDeclaration_Type(self, ctx):
            assert len(ctx.children) >= 1
            self._stack[-1].declaration_type = ctx.children[0].symbol.type

            if self._stack[-1].declaration_type == ctx.parser.ID:
                self._stack[-1].reference = ctx.children[0].symbol.text

            return self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitDeclaration_Metadata_Description(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitDeclaration_Metadata_Polymorphic(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitDeclaration_Metadata_SuppressPolymorphic(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitDeclaration_Metadata_Plural(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitStringMetadata_Validation(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitStringMetadata_MaxLength(self, ctx):
            # ---------------------------------------------------------------------------
            def Functor(value):
                if value < 0:
                    raise ParseInvalidStringLengthException( self._source_name,
                                                             ctx.start.line,
                                                             ctx.start.column + 1,
                                                             value=value,
                                                           )

            # ---------------------------------------------------------------------------
            
            self._ApplyMetadataTag(ctx, validation_functor=Functor)

        # ---------------------------------------------------------------------------
        def visitStringMetadata_MinLength(self, ctx):
            # ---------------------------------------------------------------------------
            def Functor(value):
                if value < 0:
                    raise ParseInvalidStringLengthException( self._source_name,
                                                             ctx.start.line,
                                                             ctx.start.column + 1,
                                                             value=value,
                                                           )

            # ---------------------------------------------------------------------------

            self._ApplyMetadataTag(ctx, validation_functor=Functor)

        # ---------------------------------------------------------------------------
        def visitEnumValues_Values(self, ctx):
            self._ApplyMetadataTag(ctx.children[0])
            
        # ---------------------------------------------------------------------------
        def visitEnumMetadata_FriendlyValues(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitEnum_StringList(self, ctx):
            values = []

            # ---------------------------------------------------------------------------
            def Functor(value):
                values.append(value)
                return False

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            with CallOnExit(self._stack.pop):
                self.visitChildren(ctx)

            assert callable(self._stack[-1])
            
            result = self._stack[-1](values)
            if result != False:
                self._stack.pop()

        # ---------------------------------------------------------------------------
        def visitIntegerMetadata_Bytes(self, ctx):
            # ---------------------------------------------------------------------------
            def Functor(value):
                if value < 0:
                    raise ParseInvalidIntegerBytesException( self._source_name,
                                                             ctx.start.line,
                                                             ctx.start.column + 1,
                                                             value=value,
                                                           )

            # ---------------------------------------------------------------------------

            self._ApplyMetadataTag(ctx, validation_functor=Functor)

        # ---------------------------------------------------------------------------
        def visitIntegerMetadata_Max(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitIntegerMetadata_Min(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitNumberMetadata_Max(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitNumberMetadata_Min(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitFilenameMetadata_Type(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitFilenameMetadata_MustExist(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitCustomMetadata_Type(self, ctx):
            if not observer.Flags & observer.ParseFlags.SupportCustomTypes:
                raise ParseUnsupportedCustomTypes( self._source_name,
                                                   ctx.start.line,
                                                   ctx.start.column,
                                                 )

            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitMetadata_Name(self, ctx):
            self._ApplyMetadataTag(ctx)

        # ---------------------------------------------------------------------------
        def visitArity_Optional(self, ctx):
            self._stack[-1].arity = (0, 1)

        # ---------------------------------------------------------------------------
        def visitArity_ZeroOrMore(self, ctx):
            self._stack[-1].arity = (0, None)

        # ---------------------------------------------------------------------------
        def visitArity_OneOrMore(self, ctx):
            self._stack[-1].arity = (1, None)

        # ---------------------------------------------------------------------------
        def visitArity_Custom(self, ctx):
            # '{' <value> '}'
            assert len(ctx.children) == 3

            value = int(ctx.children[1].symbol.text)
            if value < 0:
                raise ParseInvalidArityException( self._source_name,
                                                  ctx.children[1].symbol.line,
                                                  ctx.children[1].symbol.column + 1,
                                                  value=value,
                                                )

            self._stack[-1].arity = (value, value)

        # ---------------------------------------------------------------------------
        def visitArity_CustomRange(self, ctx):
            # '{' <min_value> ',' <max_value> '}'
            assert len(ctx.children) == 5

            min_value = int(ctx.children[1].symbol.text)
            max_value = int(ctx.children[3].symbol.text)

            if min_value < 0:
                raise ParseInvalidArityException( self._source_name,
                                                  ctx.children[1].symbol.line,
                                                  ctx.children[1].symbol.column + 1,
                                                  value=min_value,
                                                )

            if max_value < 0 or max_value <= min_value:
                raise ParseInvalidArityException( self._source_name,
                                                  ctx.children[3].symbol.line,
                                                  ctx.children[3].symbol.column + 1,
                                                  value=max_value,
                                                )

            self._stack[-1].arity = (min_value, max_value)

        # ---------------------------------------------------------------------------
        def visitExtension(self, ctx):
            with self._PushNewStackItem(ctx) as item:
                item.declaration_type = -ctx.parser.RULE_extension
                self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitExtension_Name(self, ctx):
            assert len(ctx.children) == 1
            name = ctx.children[0].symbol.text

            extension = next((ext for ext in observer.GetExtensions() if ext.Name == name), None)
            if not extension:
                raise ParseInvalidExtensionException( self._source_name,
                                                      ctx.start.line,
                                                      ctx.start.column + 1,
                                                      name=name,
                                                    )

            if not extension.AllowDuplicates:
                siblings = self._stack[-1].Parent.items

                for sibling in siblings:
                    if sibling.declaration_type == -ctx.parser.RULE_extension and sibling.name == name:
                        raise ParseDuplicateExtensionException( self._source_name,
                                                                ctx.start.line,
                                                                ctx.start.column + 1,
                                                                name=name,
                                                                source=sibling.Source,
                                                                line=sibling.Line,
                                                                column=sibling.Column,
                                                              )

            self._stack[-1].name = name

        # ---------------------------------------------------------------------------
        def visitExtension_Content_Positional(self, ctx):
            obj = self._stack[-1]

            # ---------------------------------------------------------------------------
            def Functor(value):
                obj.positional_arguments.append(value)
            
            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)
            self.visitChildren(ctx)

        # ---------------------------------------------------------------------------
        def visitExtension_Content_Keyword_Name(self, ctx):
            if not isinstance(ctx, antlr4.tree.Tree.TerminalNode):
                assert len(ctx.children) == 1
                ctx = ctx.children[0]

            keyword = ctx.symbol.text
            obj = self._stack[-1]

            # ---------------------------------------------------------------------------
            def Functor(value):
                if keyword in obj.keyword_arguments:
                    raise ParseDuplicateKeywordException( self._source_name,
                                                          ctx.symbol.line,
                                                          ctx.symbol.column + 1,
                                                          keyword=keyword,
                                                        )

                obj.keyword_arguments[keyword] = value

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)

        # ---------------------------------------------------------------------------
        # ---------------------------------------------------------------------------
        # ---------------------------------------------------------------------------
        @contextmanager
        def _PushNewStackItem(self, ctx):
            if ctx.start.type == ctx.parser.LBRACK:
                if not observer.Flags & observer.ParseFlags.SupportAttributes:
                    raise ParseUnsupportedAttributes( self._source_name,
                                                      ctx.start.line,
                                                      ctx.start.column + 1,
                                                    )

                item_type = Item.Type_Attribute
            elif ctx.start.type == ctx.parser.LPAREN:
                item_type = Item.Type_Definition
            else:
                item_type = Item.Type_Standard

            item = Item( item_type,
                         self._stack[-1],
                         self._source_name,
                         ctx.start.line,
                         ctx.start.column + 1,
                         is_external=self._is_external,
                       )

            self._stack[-1].items.append(item)

            self._stack.append(item)
            yield item
            self._stack.pop()

        # ---------------------------------------------------------------------------
        def _ApplyMetadataTag( self, 
                               ctx,
                               validation_functor=None,
                             ):
            if not isinstance(ctx, antlr4.tree.Tree.TerminalNode):
                assert len(ctx.children) == 1
                ctx = ctx.children[0]

            tag = ctx.symbol.text
            obj = self._stack[-1]

            # ---------------------------------------------------------------------------
            def Functor(value):
                if tag in obj.metadata:
                    raise ParseDuplicateMetadataException( self._source_name,
                                                           ctx.symbol.line,
                                                           ctx.symbol.column + 1,
                                                           tag=tag,
                                                         )

                if validation_functor:
                    validation_functor(value)

                obj.metadata[tag] = value

            # ---------------------------------------------------------------------------
            
            self._stack.append(Functor)

    # ---------------------------------------------------------------------------
    def Impl(name, antlr_stream, is_external):
        lexer = SimpleSchemaLexer(antlr_stream)
        tokens = antlr4.CommonTokenStream(lexer)

        tokens.fill()

        parser = SimpleSchemaParser(tokens)

        # ---------------------------------------------------------------------------
        class ErrorListener(antlr4.error.ErrorListener.ErrorListener):

            # ---------------------------------------------------------------------------
            def __init__(self, *args, **kwargs):
                super(ErrorListener, self).__init__(*args, **kwargs)

            # ---------------------------------------------------------------------------
            @staticmethod
            def syntaxError(recognizer, offendingSymbol, line, column, msg, e):
                raise ANTLRException( msg, 
                                      name,
                                      line,
                                      column + 1,
                                    )

        # ---------------------------------------------------------------------------
        
        parser.addErrorListener(ErrorListener())

        ast = parser.statements()

        assert ast
        ast.accept(Visitor(name, is_external))

    # ---------------------------------------------------------------------------
    
    for source_name, content_generator in source_name_content_generators.iteritems():
        antlr_stream = antlr4.InputStream(content_generator())
        antlr_stream.filename = source_name

        Impl( source_name,
              antlr_stream,
              is_external=False,
            )

    # Iterating via index rather than by element as processing the content may update the
    # list.
    index = 0

    while index < len(include_filenames):
        Impl( include_filenames[0],
              antlr4.FileStream(include_filenames[index]),
              is_external=True,
            )

        index += 1

    # ---------------------------------------------------------------------------
    def GetLiteral(value):
        value = SimpleSchemaParser.literalNames[value]

        if value[0] == "'": 
            value = value[1:]

        if value[-1] == "'":
            value = value[:-1]

        return value

    # ---------------------------------------------------------------------------
    def Postprocess(item):
        
        # Validate compound metadata
        if item.declaration_type == SimpleSchemaParser.STRING_TYPE:
            min_length = GetLiteral(SimpleSchemaParser.STRING_METADATA_MIN_LENGTH)
            max_length = GetLiteral(SimpleSchemaParser.STRING_METADATA_MAX_LENGTH)

            if ( min_length in item.metadata and 
                 max_length in item.metadata and 
                 item.metadata[max_length] < item.metadata[min_length]
               ):
                raise ParseInvalidStringLengthException( item.Source,
                                                         item.Line,
                                                         item.Column,
                                                         value=item.metadata[SimpleSchemaParser.literalNames[SimpleSchemaParser.STRING_METADATA_MAX_LENGTH]],
                                                       )

        if item.declaration_type == SimpleSchemaParser.ENUM_TYPE:
            values = GetLiteral(SimpleSchemaParser.ENUM_METADATA_VALUES)
            friendly_values = GetLiteral(SimpleSchemaParser.ENUM_METADATA_FRIENDLY_VALUES)

            if ( values in item.metadata and 
                 friendly_values in item.metadata and 
                 len(item.metadata[values]) != len(item.metadata[friendly_values])
               ):
                raise ParseMismatchedEnumValuesException( item.Source,
                                                          item.Line,
                                                          item.Column,
                                                          num_values=len(item.metadata[values]),
                                                          num_friendly_values=len(item.metadata[friendly_values]),
                                                        )

        if item.declaration_type == SimpleSchemaParser.INTEGER_TYPE:
            min_value = GetLiteral(SimpleSchemaParser.METADATA_MIN)
            max_value = GetLiteral(SimpleSchemaParser.METADATA_MAX)

            if ( min_value in item.metadata and
                 max_value in item.metadata and 
                 item.metadata[max_value] < item.metadata[min_value]
               ):
                raise ParseInvalidMaxValueException( item.Source,
                                                     item.Line,
                                                     item.Column,
                                                     value=item.metdata[max_value],
                                                   )

        if item.declaration_type == SimpleSchemaParser.NUMBER_TYPE:
            min_value = GetLiteral(SimpleSchemaParser.METADATA_MIN)
            max_value = GetLiteral(SimpleSchemaParser.METADATA_MAX)

            if ( min_value in item.metadata and
                 max_value in item.metadata and 
                 item.metadata[max_value] < item.metadata[min_value]
               ):
                raise ParseInvalidMaxValueException( item.Source,
                                                     item.Line,
                                                     item.Column,
                                                     value=item.metdata[max_value],
                                                   )

        # Resolve references
        if item.reference:
            # ---------------------------------------------------------------------------
            def FindItemByName_NoThrow(name, i):
                name_parts = name.split('.')
                    
                while i:
                    query = i
                        
                    for name_part in name_parts:
                        # Ensure that the original item doesn't appear anywhere
                        # within the item's hierarchy.
                        query = next((itm for itm in query.items if itm.name == name_part), None)
                        if not query:
                            break

                    if query:
                        return query

                    i = i.Parent

                return None

            # ---------------------------------------------------------------------------
            
            reference_name = item.reference
            if isinstance(reference_name, Item):
                assert reference_name.declaration_type == SimpleSchemaParser.ID
                assert reference_name.name == None
                    
                reference_name = reference_name.reference

            assert isinstance(reference_name, unicode)
                
            reference_item = FindItemByName_NoThrow(reference_name, item)
            if reference_item:
                item.reference.referenced_by.append(item)

                # BugBug: This doesn't work quie right (ref to ref to ref)
                if ( item.declaration_type == -SimpleSchemaParser.RULE_obj and
                     reference_item.declaration_type != -SimpleSchemaParser.RULE_obj and
                     not observer.Flags & observer.ParseFlags.SupportSimpleObjects
                   ):
                    raise ParseUnsupportedSimpleObjects( item.Source,
                                                         item.Line,
                                                         item.Column,
                                                       )
            else:
                if observer.Flags & observer.ParseFlags.ResolveReferences:
                    raise ParseInvalidReferenceException( item.Source,
                                                          item.Line,
                                                          item.Column,
                                                          name=reference_nam,
                                                      )

                reference_item = reference_name

            assert reference_item
            item.reference = reference_item
                

    # ---------------------------------------------------------------------------
    def SetSubType(item):
        if item.subtype != None:
            return

        if item.declaration_type == -SimpleSchemaParser.RULE_extension:
            item.subtype = Item.SubType_Extension

        elif item.declaration_type == -SimpleSchemaParser.RULE_obj:
            if ( item.reference == None or 
                 isinstance(item.reference, unicode) or 
                 (isinstance(item.reference, Item) and item.reference.declaration_type < 0)
               ):
                item.subtype = Item.SubType_Compound
            else:
                assert observer.Flags & observer.SupportSimpleObjects
                item.subtype = Item.SubType_Simple

                # BugBug: This doesn't work (ref to ref to ref)

                # Everything referencing this item is also a simple type (this will be
                # verified during Resolution)
                items_to_modify = list(item.referenced_by)

                while items_to_modify:
                    item_to_modify = items_to_modify.pop(0)

                    item_to_modify.subtype = Item.SubType_Simple
                    items_to_modify.extend(item_to_modify.referenced_by)

        elif item.declaration_type == SimpleSchemaParser.ID:
            # ---------------------------------------------------------------------------
            def IsAugmented():
                if item.arity != None:
                    return True

                for key in item.metadata.iterkeys():
                    if key.startswith("pragma-"):
                        continue

                    # Some values doesn't count as augmentation
                    if key in [ GetLiteral(SimpleSchemaParser.GENERIC_METADATA_PLURAL),
                                GetLiteral(SimpleSchemaParser.GENERIC_METADATA_DESCRIPTION),
                              ]:
                        continue

                    return True

                return False

            # ---------------------------------------------------------------------------
            
            item.subtype = Item.SubType_Augmented if IsAugmented() else Item.SubType_Alias

        elif item.declaration_type > 0:
            item.subtype = Item.SubType_Fundamental

        else:
            assert False

    # ---------------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            Impl(child, functor)

    # ---------------------------------------------------------------------------
    
    Impl(root, Postprocess)
    Impl(root, SetSubType)
    
    return root
