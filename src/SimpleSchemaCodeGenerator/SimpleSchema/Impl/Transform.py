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

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Package
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import TypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)   # <Redefining build-in type> pylint: disable = W0622

from . import Exceptions
from .Item import Item

from ..Elements import *
from ..Observer import *

sys.path.insert(0, os.path.join(_script_dir, "..", "Grammar", "GeneratedCode"))
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
    def CreateArity(arity):
        if arity == None:
            return Arity(1, 1)

        return Arity(*arity)

    # ---------------------------------------------------------------------------
    def CreateTypeInfo(item):
        # ---------------------------------------------------------------------------
        def Create(type, item, **mappings):
            args = {}

            for k, v in mappings.iteritems():
                key_name = Item.GetLiteral(v)

                if key_name in item.metadata:
                    args[k] = item.metadata[key_name]
                    del item.metadata[key_name]

            return type(**args)

        # ---------------------------------------------------------------------------
        
        if item.declaration_type == SimpleSchemaParser.STRING_TYPE:
            return Create( TypeInfo.StringTypeInfo,
                           item,
                           validation=SimpleSchemaParser.STRING_METADATA_VALIDATION,
                           min_length=SimpleSchemaParser.STRING_METADATA_MIN_LENGTH,
                           max_length=SimpleSchemaParser.STRING_METADATA_MAX_LENGTH,
                         )

        elif item.declaration_type == SimpleSchemaParser.ENUM_TYPE:
            return Create( TypeInfo.EnumTypeInfo,
                           item,
                           values=SimpleSchemaParser.ENUM_METADATA_VALUES,
                           friendly_values=SimpleSchemaParser.ENUM_METADATA_FRIENDLY_VALUES,
                         )

        elif item.declaration_type == SimpleSchemaParser.INTEGER_TYPE:
            return Create( TypeInfo.IntTypeInfo,
                           item,
                           min=SimpleSchemaParser.METADATA_MIN,
                           max=SimpleSchemaParser.METADATA_MAX,
                         )

        elif item.declaration_type == SimpleSchemaParser.NUMBER_TYPE:
            return Create( TypeInfo.FloatTypeInfo,
                           item,
                           min=SimpleSchemaParser.METADATA_MIN,
                           max=SimpleSchemaParser.METADATA_MAX,
                         )

        elif item.declaration_type == SimpleSchemaParser.FILENAME_TYPE:
            type_value = TypeInfo.FilenameTypeInfo.Type_File
            must_exist_value = True

            type_key = Item.GetLiteral(SimpleSchemaParser.FILENAME_METADATA_TYPE)
            if type_key in item.metadata:
                value = item.metadata[type_key]
                del item.metadata[type_key]

                if value == "file":
                    type_value = TypeInfo.FilenameTypeInfo.Type_File
                elif value == "directory":
                    type_value = TypeInfo.FilenameTypeInfo.Type_Directory
                elif value == "either":
                    type_value = TypeInfo.FilenameTypeInfo.Type_Either
                else:
                    assert False, value

            must_exist_key = Item.GetLiteral(SimpleSchemaParser.FILENAME_METADATA_MUST_EXIST)
            if must_exist_key in item.metadata:
                must_exist_value = item.metadata[must_exist_key]

            return Create( TypeInfo.FilenameTypeInfo,
                           type=type_value,
                           ensure_exists=must_exist_value,
                         )

        elif item.declaration_type == SimpleSchemaParser.CUSTOM_TYPE:
            custom_t = Item.GetLiteral(SimpleSchemaParser.CUSTOM_METADATA_T)
            assert custom_t in item.metadata

            result = item.metadata[custom_t]
            del item.metadata[custom_t]

            return result

        elif item.declaration_type == SimpleSchemaParser.BOOLEAN_TYPE:
            return TypeInfo.BoolTypeInfo()

        elif item.declaration_type == SimpleSchemaParser.GUID_TYPE:
            return TypeInfo.GuidTypeInfo()

        elif item.declaration_type == SimpleSchemaParser.DATETIME_TYPE:
            return TypeInfo.DateTimeTypeInfo()

        elif item.declaration_type == SimpleSchemaParser.TIME_TYPE:
            return TypeInfo.TimeTypeInfo()

        elif item.declaration_type == SimpleSchemaParser.DURATION_TYPE:
            return TypeInfo.DurationTypeInfo()

        else:
            raise Exception("Unexpected declaration_type")

    # ---------------------------------------------------------------------------
    def Create(item, use_cache=True):
        if ( not use_cache or
             item.key not in lookup or
             (item.subtype == Item.SubType_Extension and next(ext for ext in observer.GetExtensions() if ext.Name == item.name).AllowDuplicates)
           ):
            # Signal that we are processing this item
            lookup[item.key] = None

            # Create arity objects
            type_arity = CreateArity(item.arity)
            data_arity = None if item.ItemType == Item.ItemType_Definition else type_arity

            # Get the metadata
            additional_data = OrderedDict()
            pragma_data = OrderedDict()

            for k, v in item.metadata.iteritems():
                if k.startswith("pragma-"):
                    pragma_data[k[len("pragma-"):]] = v
                else:
                    additional_data[k] = v

            # Create the element
            element = None

            if item.subtype == Item.SubType_Extension:
                element = ExtensionElement( positional_arguments=item.positional_arguments,
                                            keyword_arguments=item.keyword_arguments,

                                            name=item.name,
                                            type_arity=type_arity,
                                            data_arity=data_arity,
                                            source=item.Source,
                                            line=item.Line,
                                            column=item.Column,
                                            is_external=item.IsExternal,
                                            additional_data=additional_data,
                                            pragma_data=pragma_data,

                                            # Secondary pass
                                            parent=None,
                                          )

            elif item.subtype == Item.SubType_Compound:
                element = CompoundElement( children=[ Create(child) for child in item.items ],
                                           base=Create(item.reference) if item.reference else None,

                                           name=item.name,
                                           type_arity=type_arity,
                                           data_arity=data_arity,
                                           source=item.Source,
                                           line=item.Line,
                                           column=item.Column,
                                           is_external=item.IsExternal,
                                           additional_data=additional_data,
                                           pragma_data=pragma_data,

                                           # Secondary pass
                                           parent=None,
                                           derived_elements=[],
                                         )

                element.secondary_pass_info = QuickObject( derived_elements=[ i for i in item.referenced_by if i.subtype == Item.SubType_Compound ],
                                                         )


            elif item.subtype == Item.SubType_Simple:
                pass # BugBug
                # BugBug # Get all the children
                # BugBug all_children = []
                # BugBug 
                # BugBug query = item
                # BugBug while query:
                # BugBug     all_children.extend(query.items)
                # BugBug     query = query.reference

            elif item.subtype == Item.SubType_Fundamental:
                element = FundamentalElement( type_info=CreateTypeInfo(item),
                                              is_attribute=item.ItemType == Item.ItemType_Attribute,

                                              name=item.name,
                                              type_arity=type_arity,
                                              data_arity=data_arity,
                                              source=item.Source,
                                              line=item.Line,
                                              column=item.Column,
                                              is_external=item.IsExternal,
                                              additional_data=additional_data,
                                              pragma_data=pragma_data,
                                            
                                              # Secondary pass
                                              parent=None,
                                            )

            elif item.subtype == Item.SubType_Alias:
                assert item.arity == None
                assert not item.is_new_type

                # Copy the referenced arity
                referenced_item = item.reference.ResolveAliases()

                type_arity = CreateArity(referenced_item.arity)
                data_arity = None if item.ItemType == Item.ItemType_Definition else type_arity

                element = AliasElement( is_new_type=False,
                                        is_attribute=item.ItemType == Item.ItemType_Attribute,

                                        name=item.name,
                                        type_arity=type_arity,
                                        data_arity=data_arity,
                                        source=item.Source,
                                        line=item.Line,
                                        column=item.Column,
                                        is_external=item.IsExternal,
                                        additional_data=additional_data,
                                        pragma_data=pragma_data,

                                        # Secondary pass
                                        parent=None,
                                        reference=None,
                                      )

                element.secondary_pass_info = QuickObject( reference=item.reference,
                                                         )

            elif item.subtype == Item.SubType_Augmented:
                # Copy the referenced arity (if necessary)
                if item.arity == None and not item.is_new_type:
                    referenced_item = item.reference.ResolveAliases()

                    type_arity = CreateArity(referenced_item.arity)
                    data_arity = None if item.ItemType == Item.ItemType_Definition else type_arity

                element = AugmentedElement( is_new_type=item.is_new_type,
                                            is_attribute=item.ItemType == Item.ItemType_Attribute,
                                            was_arity_explicitly_provided=item.arity != None,

                                            name=item.name,
                                            type_arity=type_arity,
                                            data_arity=data_arity,
                                            source=item.Source,
                                            line=item.Line,
                                            column=item.Column,
                                            is_external=item.IsExternal,
                                            additional_data=additional_data,
                                            pragma_data=pragma_data,

                                            # Secondary pass
                                            parent=None,
                                            reference=None,
                                          )

                element.secondary_pass_info = QuickObject( reference=item.reference,
                                                         )

            else:
                raise Exception("Unexpected subtype")

            assert element

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
        if not hasattr(element, "secondary_pass_info"):
            return

        spi = element.secondary_pass_info
        del element.secondary_pass_info

        for name, value in spi.__dict__.iteritems():
            if name == "derived_elements":
                for potential_derived_item in value:
                    potential_derived_element = lookup[potential_derived_item.key]

                if next((child for child in potential_derived_element.Children if child.DataArity), None):
                    element.DerivedElements.append(potential_derived_element)

                if element.polymorphic and not potential_derived_element.suppress_polymorphic:
                    potential_derived_element.polymorphic = True

            elif name == "reference":
                element.Reference = lookup[value]
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
    
    root_element = Create(root)

    ResolveParents(root_element, None)
    SecondaryPass(root_element)

    return root_element
