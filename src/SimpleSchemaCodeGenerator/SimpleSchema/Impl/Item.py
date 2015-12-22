# ---------------------------------------------------------------------------
# |  
# |  Item.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/05/2015 03:08:18 PM
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

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.TypeInfo import *

from ..Metadata import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "..", "..", "Grammars", "GeneratedCode"))
assert os.path.isdir(sys.path[0]), sys.path[0]

with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaParser import SimpleSchemaParser                       # <Unable to import> pylint: disable = F0401

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Item(object):

    ( ItemType_Standard, 
      ItemType_Attribute, 
      ItemType_Definition,
    ) = range(3)

    ( SubType_Extension,
      SubType_Compound,
      SubType_Simple,
      SubType_Fundamental,
      SubType_Alias,
      SubType_Augmented,
    ) = range(6)

    # ---------------------------------------------------------------------------
    def __init__( self,
                  item_type,
                  parent,
                  source,
                  line,
                  column,
                  is_external,
                ):
        # Populated during Parse
        self.ItemType                       = item_type
        self.Parent                         = parent
        self.Source                         = source
        self.Line                           = line
        self.Column                         = column
        self.IsExternal                     = is_external
        
        self.name                           = None
        self.declaration_type               = None
        self.reference                      = None
        self.metadata                       = OrderedDict()
        self.arity                          = None
        self.items                          = []

        self.positional_arguments           = []
        self.keyword_arguments              = OrderedDict()
        
        # Populated during Validation
        self.referenced_by                  = []

        # Populated during Commit
        self._is_committed                  = False
        self.subtype                        = None
        self.key                            = None
        self.is_new_type                    = None

    # ---------------------------------------------------------------------------
    @property
    def IsCommitted(self):
        return self._is_committed
    
    # ---------------------------------------------------------------------------
    def __setattr__(self, key, value):
        # Ensure that values aren't being set after an object
        # has been committed
        if getattr(self, "_is_committed", False):
            raise Exception("The object has been committed - no further changes are permitted")

        return super(Item, self).__setattr__(key, value)

    # ---------------------------------------------------------------------------
    def Commit(self, observer, subtype):
        self.subtype = subtype

        # Assign the key
        assert self.key == None
    
        names = []
    
        item = self
        while item:
            names.append(item.name)
            item = item.Parent
    
        names.reverse()
    
        # Don't include the root element
        self.key = tuple(names[1:])
    
        # Determine if we are looking at a new type
        assert self.is_new_type == None
    
        if self.subtype in [ self.SubType_Alias, self.SubType_Augmented, ]:
            assert self.reference
            assert self.reference.IsCommitted

            # ---------------------------------------------------------------------------
            def CalcIsNewType():
                is_fundamental_reference = self.reference.ResolveAugmentations().subtype == self.SubType_Fundamental

                # If...
                #   An arity was provided and...                                                    (1)
                #       The arity was not an optional arity or...                                   (2)
                #       The arity was an optional arity and optional arities represent new types    (3)
                if ( self.arity != None and 
                     ( not self.arity.IsOptional or 
                       observer.DoesOptionalReferenceRepresentNewType(is_fundamental_reference)
                     )
                   ):
                    return True

                # If here, we need to see if there is any metadata associated with this item whose 
                # presense indicates that we are looking at a new type.
                metadata = self._GetMetadataImpl(observer)

                for md in itertools.chain(metadata.required, metadata.optional):
                    if md.IsNewType and md.Name in self.metadata:
                        return True

                return False

            # ---------------------------------------------------------------------------
            
            self.is_new_type = CalcIsNewType()
    
        else:
            self.is_new_type = True
    
        assert self._is_committed == False
        self._is_committed = True

    # ---------------------------------------------------------------------------
    def Walk( self,
              callback,                     # def Func(item) -> False to terminate iteration
            ):
        assert self.IsCommitted

        item = self

        while True:
            if callback(item) == False:
                return False

            if item.reference == None:
                break

            item = item.reference

        return True
    
    # ---------------------------------------------------------------------------
    def ResolveAliases(self):
        result = [ None, ]
    
        # ---------------------------------------------------------------------------
        def Callback(item):
            result[0] = item
            return item.subtype == self.SubType_Alias
    
        # ---------------------------------------------------------------------------
        
        self.Walk(Callback)
    
        assert result[0]
        return result[0]

    # ---------------------------------------------------------------------------
    def ResolveAugmentations(self):
        assert self.IsCommitted

        result = [ None, ]

        # ---------------------------------------------------------------------------
        def Callback(item):
            result[0] = item
            return item.subtype in [ self.SubType_Alias, self.SubType_Augmented, ]

        # ---------------------------------------------------------------------------
        
        self.Walk(Callback)

        assert result[0]
        return result[0]

    # ---------------------------------------------------------------------------
    def GetPotentialMetadata(self, observer):
        assert self.IsCommitted

        result = self._GetMetadataImpl(observer)

        # If we are looking at an augmented item, combine the metadata
        # of the item and the item that it augments.
        if self.subtype in [ self.SubType_Alias, self.SubType_Augmented, ] and not self.is_new_type:
            assert self.reference
            referenced_result = self.reference.GetPotentialMetadata(observer)
            
            for md in itertools.chain(referenced_result.required, referenced_result.optional):
                if not any(md.Name == item.Name for item in itertools.chain(referenced_result.required, referenced_result.optional)):
                    result.optional.append(md)

        return result

    # ---------------------------------------------------------------------------
    def _GetMetadataImpl(self, observer):
        result = QuickObject( required=[],
                              optional=list(UNIVERSAL_METADATA),
                            )

        metadata_map = { SimpleSchemaParser.STRING_TYPE : STRING_METADATA,
                         SimpleSchemaParser.ENUM_TYPE : ENUM_METADATA,
                         SimpleSchemaParser.INTEGER_TYPE : INTEGER_METADATA,
                         SimpleSchemaParser.NUMBER_TYPE : NUMBER_METADATA,
                         SimpleSchemaParser.FILENAME_TYPE : FILENAME_METADATA,
                         SimpleSchemaParser.CUSTOM_TYPE : CUSTOM_METADATA,
                       }

        # ---------------------------------------------------------------------------
        def ApplyFundamentalItems(declaration_type):
            if declaration_type in metadata_map:
                required, optional = metadata_map[declaration_type]
                
                result.required.extend(required)
                result.optional.extend(optional)    

        # ---------------------------------------------------------------------------
        
        if self.subtype == self.SubType_Compound:
            result.optional.extend(COMPOUND_METADATA)
        
        elif self.subtype == self.SubType_Fundamental:
            assert isinstance(self.declaration_type, int) and self.declaration_type > 0, self.declaration_type
            ApplyFundamentalItems(self.declaration_type)

        if self.arity:
            if self.arity.IsOptional:
                result.optional.extend(OPTIONAL_METADATA)
                
            if self.arity.IsCollection:
                result.optional.extend(COLLECTION_METADATA)

        return result
