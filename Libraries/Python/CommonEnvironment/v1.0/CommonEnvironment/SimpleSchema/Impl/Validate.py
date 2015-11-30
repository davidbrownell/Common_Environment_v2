# ---------------------------------------------------------------------------
# |  
# |  Validate.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/25/2015 04:21:00 PM
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

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Package
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment.TypeInfo import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)   # <Redefining build-in type> pylint: disable = W0622

from ..Exceptions import *
from ..Observer import *

from .Item import *

sys.path.insert(0, os.path.join(_script_dir, "..", "Grammar", "GeneratedCode"))
assert os.path.isdir(sys.path[0]), sys.path[0]

with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaParser import SimpleSchemaParser                       # <Unable to import> pylint: disable = F0401

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def Validate(root, observer):
    
    # ---------------------------------------------------------------------------
    def FindItemByName_NoThrow(name, item):
        name_parts = name.split('.')

        while item:
            query = item

            for name_part in name_parts:
                query = next((i for i in query.items if i.name == name_part), None)
                if not query:
                    break

            if query:
                return query

            item = item.Parent

        return None

    # ---------------------------------------------------------------------------
    def ResolveReferences(item):
        if not isinstance(item.reference, unicode):
            return

        assert item.declaration_type == SimpleSchemaParser.ID
        item.declaration_type = 0

        if not observer.Flags & Observer.ParseFlags.ResolveReferences:
            return

        referenced_item = FindItemByName_NoThrow(item.reference, item)
        if not referenced_item:
            raise ValidateInvalidReferenceException( item.Source,
                                                     item.Line,
                                                     item.Column,
                                                     name=item.reference,
                                                   )

        item.reference = referenced_item
        referenced_item.referenced_by.append(item)

    # ---------------------------------------------------------------------------
    def Commit(item, stack=None):
        stack = stack or []

        if item in stack:
            raise ValidateCircularDependencyException( item.Source,
                                                       item.Line,
                                                       item.Column,
                                                       info=StreamDecorator.LeftJustify( '\n'.join([ "- {name} ({source} [{line} <{column}>])".format
                                                                                                         (
                                                                                                           name=i.name,
                                                                                                           source=i.Source,
                                                                                                           line=i.Line,
                                                                                                           column=i.Column,
                                                                                                         )
                                                                                                     for i in stack + [ item, ] 
                                                                                                   ]).rstrip(),
                                                                                         4,
                                                                                         skip_first_line=False,
                                                                                       ),
                                                     )

        if item.IsCommitted:
            return

        # Ensure that all referenced items are committed before continuing
        if isinstance(item.reference, item):
            stack.append(item)
            with CallOnExit(stack.pop):
                Commit(item.reference, stack)

        # Calculate the subtype
        subtype = None

        if item.declaration_type == -SimpleSchemaParser.RULE_extension:
            subtype = Item.SubType_Extension

        elif item.declaration_type == -SimpleSchemaParser.RULE_obj:
            # ---------------------------------------------------------------------------
            def IsSimple():
                # A simple object will ultimately reference a fundamental type
                ref = item.reference

                while isinstance(ref, Item):
                    assert ref.subtype != None

                    if ref.subtype in [ Item.SubType_Simple, Item.SubType_Fundamental, ]:
                        return True

                    if ref.subtype == Item.SubType_Compound:
                        break

                    ref = ref.reference

                return False

            # ---------------------------------------------------------------------------
            
            if IsSimple():
                if not observer.Flags & Observer.ParseFlags.SupportSimpleObjects:
                    raise ValidateUnsupportedSimpleObjectsException( item.Source,
                                                                     item.Line,
                                                                     item.Column,
                                                                   )

                for child in item.items:
                    if child.ItemType != Item.ItemType_Attribute:
                        raise ValidateInvalidSimpleObjectChildException( child.Source,
                                                                         child.Line,
                                                                         child.Column,
                                                                       )

                subtype = Item.SubType_Simple
            else:
                subtype = Item.SubType_Compound

        elif item.declaration_type == 0:
            # ---------------------------------------------------------------------------
            def IsAugmented():
                if item.arity != None:
                    return True

                for key in item.metadata.iterkeys():
                    if key.startswith("pragma-"):
                        continue

                    # Some values don't cound as augmentation
                    if key in [ Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_PLURAL),
                                Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_DESCRIPTION),
                              ]:
                        continue

                    return True

                return False

            # ---------------------------------------------------------------------------
            
            if IsAugmented():
                if not observer.Flags & Observer.ParseFlags.SupportAugmentations:
                    raise ValidateUnsupportedAugmentationsException( item.Source,
                                                                     item.Line,
                                                                     item.Column,
                                                                   )

                subtype = Item.SubType_Augmented
            else:
                if not observer.Flags & Observer.ParseFlags.SupportAliases:
                    raise ValidateUnsupportedAliasesException( item.Source,
                                                               item.Line,
                                                               item.Column,
                                                             )

                subtype = Item.SubType_Alias

        elif item.declaration_type > 0:
            assert not item.items
            assert not item.reference

            subtype = Item.SubType_Fundamental

        else:
            raise Exception("Unexpected subtype calculation")

        assert subtype != None
        item.Commit(observer, subtype)

    # ---------------------------------------------------------------------------
    def EnsureUniqueNames(item):
        # Ensure that names are unique
        names = {}

        i = item
        while isinstance(i, Item):
            for child in item.items:
                # No need to check extensions if duplicates are allowed or we aren't looking
                # at the root object.
                if child.subtype == Item.SubType_Extension and (i != item or next(ext for ext in observer.GetExtensions() if ext.Name == child.name).AllowDuplicates):
                    continue

                if child.name in names:
                    raise ValidateDuplicateNameException( names[child.name].Source,
                                                          names[child.name].Line,
                                                          names[child.name].Column,
                                                          name=child.name,
                                                          source=child.Source,
                                                          line=child.Line,
                                                          column=child.Column,
                                                        )

                names[child.name] = child

            i = i.reference

    # ---------------------------------------------------------------------------
    def ResolveMetadata(item):
        config_data = root.config.get(observer.Name, {})
        metadata = item.GetPotentialMetadata(observer)

        # Augment the existing metadata (if necessary)
        for md in itertools.chain(metadata.required, metadata.optional):
            if md.name not in item.metadata:
                # Can we provide a config value for this item?
                if observer.Name in root.config and md.Name in root.config[observer.Name]:
                    item.metadata[md.Name] = root.config[observer.Name][md.Name]

                elif md.DefaultValue != None:
                    # Only apply default values to references if the value is
                    # dynamically calculated. Otherwise, skip it as the value 
                    # from the referenced element will be applied to this one
                    # during element transformation.
                    if ( item.subtype in [ Item.SubType_Alias, Item.SubType_Augmented, ] and
                         not item.is_new_type and
                         not md.IsDynamicDefaultValue
                       ):
                        continue

                    item.metadata[md.Name] = md.ApplyDefault(item)
        
        # Validate compound metadata for fundamental types
        if item.subtype == Item.SubType_Fundamental:
            if item.declaration_type == SimpleSchemaParser.STRING_TYPE:
                min_length = Item.GetLiteral(SimpleSchemaParser.STRING_METATDATA_MIN_LENGTH)
                max_length = Item.GetLiteral(SimpleSchemaParser.STRING_METATDATA_MAX_LENGTH)

                for metadata_name in [ min_length, max_length, ]:
                    if isinstance(item.metadata.get(metadata_name, None), list):
                        raise ValidateDuplicateMetadataException( item.Source,
                                                                  item.Line,
                                                                  item.Column,
                                                                  name=metadata_name,
                                                                )

                if ( min_length in item.metadata and 
                     max_length in item.metadata and 
                     item.metadata[max_length] < item.metadata[min_length]
                   ):
                    raise ValidateInvalidStringLengthException( item.Source,
                                                                item.Line,
                                                                item.Column,
                                                                value=item.metadata[max_length],
                                                              )

            elif item.declaration_type == SimpleSchemaParser.ENUM_TYPE:
                values = Item.GetLiteral(SimpleSchemaParser.ENUM_METADATA_VALUES)
                friendly_values = Item.GetLiteral(SimpleSchemaParser.ENUM_METADATA_FRIENDLY_VALUES)

                if ( values in item.metadata and 
                     friendly_values in item.metadata and 
                     len(item.metadata[values]) != len(item.metadata[friendly_values])
                   ):
                    raise ValidateMismatchedEnumValuesException( item.Source,
                                                                 item.Line,
                                                                 item.Column,
                                                                 num_values=len(item.metadata[values]),
                                                                 num_friendly_values=len(item.metadata[friendly_values]),
                                                               )

            elif item.declaration_type in [ SimpleSchemaParser.METADATA_MIN, SimpleSchemaParser.METADATA_MAX, ]:
                min_value = Item.GetLiteral(SimpleSchemaParser.METADATA_MIN)
                max_value = Item.GetLiteral(SimpleSchemaParser.METADATA_MAX)

                for metadata_name in [ min_value, max_value, ]:
                    if isinstance(item.metadata.get(metadata_name, None), list):
                        raise ValidateDuplicateMetadataException( item.Source,
                                                                  item.Line,
                                                                  item.Column,
                                                                  name=metadata_name,
                                                                )

                if ( min_value in item.metadata and
                     max_value in item.metadata and 
                     item.metadata[max_value] < item.metadata[min_value]
                   ):
                    raise ValidateInvalidMaxValueException( item.Source,
                                                            item.Line,
                                                            item.Column,
                                                            value=item.metadata[max_value],
                                                          )

        # Ensure that valid metadata has been provided
        metadata_names = { md.Name for md in itertools.chain(metadata.required, metadata.optional) }

        for k in item.metadata.keys():
            if k.startswith("pragma-"):
                continue

            if k not in metadata_names:
                raise ValidateMetadataInvalidException( item.Source,
                                                        item.Line,
                                                        item.Column,
                                                        name=k,
                                                      )


        # Ensure all the required attributes are present
        for md in metadata.required:
            if md.Name not in item.metadata:
                raise ValidateMetdataRequiredException( item.Source,
                                                        item.Line,
                                                        item.Column,
                                                        name=md.Name,
                                                      )

        if Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_PLURAL) in item.metadata:
            if item.name == None:
                raise ValidateMetadataPluralNoneException( item.Source,
                                                           item.Line,
                                                           item.Column,
                                                         )

            if item.arity == None or item.arity[1] == 1:
                raise ValidateMetadataPluralSingleElementException( item.Source,
                                                                    item.Line,
                                                                    item.Column,
                                                                  )

        if Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_DEFAULT) in item.metadata:
            if item.arity != (0, 1):
                raise ValidateMetadataDefaultException( item.Source,
                                                        item.Line,
                                                        item.Column,
                                                      )
                                                      
        if Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_POLYMORPHIC) in item.metadata:
            if item.ResolveAugmentations().subtype != Item.SubType_Compound or not item.referenced_by:
                raise ValidateMetadataPolymorphicException( item.Source,
                                                            item.Line,
                                                            item.Column,
                                                          )

        if Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_SUPPRESS_POLYMORPHIC) in item.metadata:
            # ---------------------------------------------------------------------------
            def IsError():
                if item.ResolveAugmentations().subtype != Item.SubType_Compound:
                    return True

                polymorphic = Item.GetLiteral(SimpleSchemaParser.GENERIC_METADATA_POLYMORPHIC)

                # ---------------------------------------------------------------------------
                def Callback(i):
                    if polymorphic in i.metadata:
                        return False

                    return True

                # ---------------------------------------------------------------------------
                
                if item.Walk(Callback):
                    return True

                return False

            # ---------------------------------------------------------------------------
            
            if IsError():
                raise ValidateMetadataSuppressPolymorphicException( item.Source,
                                                                    item.Line,
                                                                    item.Column,
                                                                  )

        # Convert metadata values
        for md in itertools.chain(metadata.required, metadata.optional):
            if md.Name not in item.metadata:
                continue

            try:
                value = item.metadata[md.Name]

                if isinstance(value, (str, unicode)):
                    item.metadata[md.Name] = md.TypeInfo.FromString(value)
                else:
                    md.TypeInfo.Validate(value)

            except TypeInfo.ValidationException, ex:
                raise ValidateInvalidMetadataException( item.Source,
                                                        item.Line,
                                                        item.Column,
                                                        name=md.Name,
                                                        info=str(ex),
                                                      )

    # ---------------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            Impl(child, functor)

    # ---------------------------------------------------------------------------
    
    Impl(root, ResolveReferences)
    Impl(root, Commit)
    Impl(root, EnsureUniqueNames)
    Impl(root, ResolveMetadata)
    
    return root
