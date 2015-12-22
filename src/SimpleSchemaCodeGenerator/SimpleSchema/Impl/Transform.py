# ---------------------------------------------------------------------------
# |  
# |  Transform.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/27/2015 11:40:21 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from collections import OrderedDict

from CommonEnvironment import Antlr4Helpers
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Package
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import TypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)   # <Redefining build-in type> pylint: disable = W0622

from .Item import Item

from ..Elements import *
from .. import Exceptions
from ..Observer import *

sys.path.insert(0, os.path.join(_script_dir, "..", "..", "Grammars", "GeneratedCode"))
assert os.path.isdir(sys.path[0]), sys.path[0]

with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaParser import SimpleSchemaParser                       # <Unable to import> pylint: disable = F0401

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def Transform(root, observer):
    
    lookup = {}

    # ---------------------------------------------------------------------------
    def Create(item, use_cache=True):
        if ( not use_cache or
             item.key not in lookup or
             (item.subtype == Item.SubType_Extension and next(ext for ext in observer.GetExtensions() if ext.Name == item.name).AllowDuplicates)
           ):
            # Signal that we are processing this item
            lookup[item.key] = None
            
            # Get the metadata
            additional_data = OrderedDict()
            pragma_data = OrderedDict()

            for k, v in item.metadata.iteritems():
                if k.startswith("pragma-"):
                    pragma_data[k[len("pragma-"):]] = v
                else:
                    additional_data[k] = v

            # Create the element
            is_definition_only = item.ItemType == Item.ItemType_Definition
            element = None

            if item.subtype == Item.SubType_Extension:
                element = ExtensionElement( arity=item.arity,
                                            positional_arguments=item.positional_arguments,
                                            keyword_arguments=item.keyword_arguments,

                                            name=item.name,
                                            source=item.Source,
                                            line=item.Line,
                                            column=item.Column,
                                            is_definition_only=is_definition_only,
                                            is_external=item.IsExternal,
                                            additional_data=additional_data,
                                            pragma_data=pragma_data,

                                            # Secondary pass
                                            parent=None,
                                          )

            elif item.subtype == Item.SubType_Compound:
                element = CompoundElement( children=[ Create(child) for child in item.items ] ,
                                           base=Create(item.reference) if item.reference else None,

                                           name=item.name,
                                           source=item.Source,
                                           line=item.Line,
                                           column=item.Column,
                                           is_definition_only=is_definition_only,
                                           is_external=item.IsExternal,
                                           additional_data=additional_data,
                                           pragma_data=pragma_data,

                                           # Secondary pass
                                           parent=None,
                                           type_info=None,
                                           derived_elements=[],
                                         )

                element.secondary_pass_info = QuickObject( derived_elements=[ i for i in item.referenced_by if i.subtype == Item.SubType_Compound ],
                                                         )

            elif item.subtype == Item.SubType_Simple:
                element = SimpleElement( children=[ Create(child) for child in item.items ],

                                         name=item.name,
                                         source=item.Source,
                                         line=item.Line,
                                         column=item.Column,
                                         is_definition_only=is_definition_only,
                                         is_external=item.IsExternal,
                                         additional_data=additional_data,
                                         pragma_data=pragma_data,

                                         # Secondary pass
                                         parent=None,
                                         type_info=None,
                                         children_type_info=None,
                                       )

            elif item.subtype == Item.SubType_Fundamental:
                element = FundamentalElement( is_attribute=item.ItemType == Item.ItemType_Attribute,

                                              name=item.name,
                                              source=item.Source,
                                              line=item.Line,
                                              column=item.Column,
                                              is_definition_only=is_definition_only,
                                              is_external=item.IsExternal,
                                              additional_data=additional_data,
                                              pragma_data=pragma_data,
                                            
                                              # Secondary pass
                                              parent=None,
                                              type_info=None,
                                            )

            elif item.subtype == Item.SubType_Alias:
                assert not item.is_new_type

                element = AliasElement( is_new_type=False,
                                        is_attribute=item.ItemType == Item.ItemType_Attribute,

                                        name=item.name,
                                        source=item.Source,
                                        line=item.Line,
                                        column=item.Column,
                                        is_definition_only=is_definition_only,
                                        is_external=item.IsExternal,
                                        additional_data=additional_data,
                                        pragma_data=pragma_data,

                                        # Secondary pass
                                        parent=None,
                                        type_info=None,
                                        reference=None,
                                      )

                element.secondary_pass_info = QuickObject( reference=item.reference,
                                                         )

            elif item.subtype == Item.SubType_Augmented:
                element = AugmentedElement( is_new_type=item.is_new_type,
                                            is_attribute=item.ItemType == Item.ItemType_Attribute,
                                            was_arity_explicitly_provided=item.arity != None,

                                            name=item.name,
                                            source=item.Source,
                                            line=item.Line,
                                            column=item.Column,
                                            is_definition_only=is_definition_only,
                                            is_external=item.IsExternal,
                                            additional_data=additional_data,
                                            pragma_data=pragma_data,

                                            # Secondary pass
                                            parent=None,
                                            type_info=None,
                                            reference=None,
                                          )

                element.secondary_pass_info = QuickObject( reference=item.reference,
                                                         )

            else:
                raise Exception("Unexpected subtype")

            assert element
            element._item = item

            if not use_cache:
                return element

            lookup[item.key] = element

        assert item.key in lookup
        return lookup[item.key]

    # ---------------------------------------------------------------------------
    def ResolveParents(element, parent):
        assert element.Parent == None
        element.Parent = parent

        for child in getattr(element, "Children", []):
            ResolveParents(child, element)

    # ---------------------------------------------------------------------------
    def SecondaryPass(element):
        if hasattr(element, "secondary_pass_info"):
            spi = element.secondary_pass_info
            del element.secondary_pass_info
            
            for name, value in spi.__dict__.iteritems():
                if name == "derived_elements":
                    for potential_derived_item in value:
                        potential_derived_element = lookup[potential_derived_item.key]
            
                        if next((child for child in potential_derived_element.Children if not child.IsDefinitionOnly), None):
                            element.DerivedElements.append(potential_derived_element)
            
                        if element.polymorphic and not potential_derived_element.suppress_polymorphic:
                            potential_derived_element.polymorphic = True
            
                elif name == "reference":
                    element.Reference = lookup[value.key]
                    assert element.Reference
            
                    # As a convenience, migrate all metadata from the referenced item
                    # to this one.
                    if not element.IsNewType:
                        # Ensure that the referenced element is fully populated before 
                        # copying its metadata
                        SecondaryPass(element.Reference)
            
                        for k, v in element.Reference.AdditionalData.iteritems():
                            if k not in element.AdditionalData:
                                element.AdditionalData[k] = v
                                setattr(element, k, v)
            
                        for k, v in element.Reference.PragmaData.iteritems():
                            if k not in element.PragmaData:
                                element.PragmaData[k] = v
            
                else:
                    assert False, name

        for child in getattr(element, "Children", []):
            SecondaryPass(child)

    # ---------------------------------------------------------------------------
    def ApplyTypeInfo(element):
        if isinstance(element, ExtensionElement):
            return

        if element.TypeInfo != None:
            return

        # ---------------------------------------------------------------------------
        def PopDataItem(name):
            if name in element.AdditionalData:
                value = element.AdditionalData[name]

                del element.AdditionalData[name]
                delattr(element, name)

                return value

        # ---------------------------------------------------------------------------
        def CreateTypeInfoImpl(type_, **arg_mappings):
            args = {}

            for k, v in arg_mappings.iteritems():
                value = PopDataItem(Antlr4Helpers.GetLiteral(SimpleSchemaParser, v))
                if value != None:
                    args[k] = value
                    
            return type_(arity=element._item.arity, **args)

        # ---------------------------------------------------------------------------
        def CreateFundamentalTypeInfo(declaration_type):
            if declaration_type == SimpleSchemaParser.STRING_TYPE:
                return CreateTypeInfoImpl( TypeInfo.StringTypeInfo,
                                           validation=SimpleSchemaParser.STRING_METADATA_VALIDATION,
                                           min_length=SimpleSchemaParser.STRING_METADATA_MIN_LENGTH,
                                           max_length=SimpleSchemaParser.STRING_METADATA_MAX_LENGTH,
                                         )

            elif declaration_type == SimpleSchemaParser.ENUM_TYPE:
                return CreateTypeInfoImpl( TypeInfo.EnumTypeInfo,
                                           values=SimpleSchemaParser.ENUM_METADATA_VALUES,
                                           friendly_values=SimpleSchemaParser.ENUM_METADATA_FRIENDLY_VALUES,
                                         )

            elif declaration_type == SimpleSchemaParser.INTEGER_TYPE:
                return CreateTypeInfoImpl( TypeInfo.IntTypeInfo,
                                           min=SimpleSchemaParser.METADATA_MIN,
                                           max=SimpleSchemaParser.METADATA_MAX,
                                         )

            elif declaration_type == SimpleSchemaParser.NUMBER_TYPE:
                return CreateTypeInfoImpl( TypeInfo.FloatTypeInfo,
                                           min=SimpleSchemaParser.METADATA_MIN,
                                           max=SimpleSchemaParser.METADATA_MAX,
                                         )

            elif declaration_type == SimpleSchemaParser.FILENAME_TYPE:
                type_value = TypeInfo.FilenameTypeInfo.Type_File
                must_exist_value = True

                value = PopDataItem(Antlr4Helpers.GetLiteral(SimpleSchemaParser, SimpleSchemaParser.FILENAME_METADATA_TYPE))
                if value != None:
                    if value == "file":
                        type_value = TypeInfo.FilenameTypeInfo.Type_File
                    elif value == "directory":
                        type_value = TypeInfo.FilenameTypeInfo.Type_Directory
                    elif value == "either":
                        type_value = TypeInfo.FilenameTypeInfo.Type_Either
                    else:
                        assert False, value

                value = PopDataItem(Antlr4Helpers.GetLiteral(SimpleSchemaParser, SimpleSchemaParser.FILENAME_METADATA_MUST_EXIST))
                if value != None:
                    must_exist_key = value
                
                return CreateTypeInfoImpl( TypeInfo.FilenameTypeInfo,
                                           type=type_value,
                                           ensure_exists=must_exist_value,
                                         )

            elif declaration_type == SimpleSchemaParser.CUSTOM_TYPE:
                value = PopDataItem(Antlr4Helpers.GetLiteral(SimpleSchemaParser, SimpleSchemaParser.CUSTOM_METADATA_T))
                assert value != None

                return value

            elif declaration_type == SimpleSchemaParser.BOOLEAN_TYPE:
                return CreateTypeInfoImpl(TypeInfo.BoolTypeInfo)

            elif declaration_type == SimpleSchemaParser.GUID_TYPE:
                return CreateTypeInfoImpl(TypeInfo.GuidTypeInfo)

            elif declaration_type == SimpleSchemaParser.DATETIME_TYPE:
                return CreateTypeInfoImpl(TypeInfo.DateTimeTypeInfo)

            elif declaration_type == SimpleSchemaParser.DATE_TYPE:
                return CreateTypeInfoImpl(TypeInfo.DateTypeInfo)

            elif declaration_type == SimpleSchemaParser.TIME_TYPE:
                return CreateTypeInfoImpl(TypeInfo.TimeTypeInfo)

            elif declaration_type == SimpleSchemaParser.DURATION_TYPE:
                return CreateTypeInfoImpl(TypeInfo.DurationTypeInfo)

            else:
                raise Exception("Unexpected declaration_type")

        # ---------------------------------------------------------------------------
        
        if isinstance(element, FundamentalElement):
            element.TypeInfo = CreateFundamentalTypeInfo(element._item.declaration_type)

        elif isinstance(element, CompoundElement):
            child_type_info = OrderedDict()

            for child in element.Children:
                ApplyTypeInfo(child)

                if not isinstance(child, ExtensionElement) and not child.IsDefinitionOnly:
                    child_type_info[child.Name] = child.TypeInfo
            
            element.TypeInfo = TypeInfo.ClassTypeInfo( items=child_type_info,
                                                       arity=element._item.arity,
                                                     )

        elif isinstance(element, SimpleElement):
            element.TypeInfo = CreateFundamentalTypeInfo(element._item.reference)

            child_type_info = OrderedDict()

            for child in element.Children:
                ApplyTypeInfo(child)

                if not child.IsDefinitionOnly:
                    child_type_info[child.Name] = child.TypeInfo

            element.AttributeTypeInfo = TypeInfo.ClassTypeInfo( items=child_type_info,
                                                                arity=element._item.arity,
                                                              )


        elif isinstance(element, AliasElement):
            ApplyTypeInfo(element.Reference)
            element.TypeInfo = element.Reference.TypeInfo

        elif isinstance(element, AugmentedElement):
            ApplyTypeInfo(element.Reference)
            
            new_type_info = copy.deepcopy(element.Reference.TypeInfo)
            
            if element._item.arity != None:
                new_type_info.Arity = element._item.arity

            element.TypeInfo = new_type_info

        else:
            raise Exception("Unexpected element type")

    # ---------------------------------------------------------------------------
    def Cleanup(element):
        del element._item

        for child in getattr(element, "Children", []):
            Cleanup(child)

    # ---------------------------------------------------------------------------
    
    root_element = Create(root)

    ResolveParents(root_element, None)
    SecondaryPass(root_element)
    ApplyTypeInfo(root_element)
    Cleanup(root_element)

    return root_element
