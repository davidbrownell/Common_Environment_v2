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

from CommonEnvironment.QuickObject import QuickObject

from ..Metadata import Metadata, \
                       UNIVERSAL_METADATA, \
                       COMPOUND_METADATA, \
                       COLLECTION_METADATA

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Item(object):

    ( Type_Standard, 
      Type_Attribute, 
      Type_Definition,
    ) = range(3)

    ( SubType_Extension,
      SubType_Config,
      SubType_Compound,
      SubType_Simple,
      SubType_Alias,
      SubType_Augmented,
      SubType_Fundamental,
    ) = range(7)

    # ---------------------------------------------------------------------------
    def __init__( self,
                  item_type,
                  parent,
                  source,
                  line,
                  column,
                  is_external,
                ):
        self._is_committed                  = False

        # Populated in Parse.py
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
        
        self.subtype                        = None

        # Populated in Resolve.py
        self.fundamental_or_item            = None
        self.referenced_by                  = []

        # Populated during Commit
        self.key                            = None
        self.is_new_type                    = None

    # ---------------------------------------------------------------------------
    @property
    def ItemSubType(self):
        return self.subtype

    # ---------------------------------------------------------------------------
    def __setattr__(self, key, value):
        # Ensure that values aren't being set after an object
        # has been committed
        if getattr(self, "_is_committed", False):
            raise Exception("The object has been committed - no further changes are permitted")

        return super(Item, self).__setattr__(key, value)

    # ---------------------------------------------------------------------------
    def Commit(self, observer):
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

        if self.item_type in [ ItemType.Alias, ItemType.Augmented, ]:
            # ---------------------------------------------------------------------------
            def CalcIsNewType():
                pass

            # ---------------------------------------------------------------------------
            
            self.is_new_type = CalcIsNewType()

        else:
            self.is_new_type = True

        assert self._is_committed == False
        self._is_committed = True

    # ---------------------------------------------------------------------------
    def HasReference(self):
        return isinstance(self.fundamental_or_item, Item)

    # ---------------------------------------------------------------------------
    def IsFundamental(self):
        return self.fundamental_or_item and not self.HasReference()

    # ---------------------------------------------------------------------------
    def Walk( self,
              callback,                     # def Func(item) -> False to terminate iteration
            ):
        assert self._is_committed

        item = self

        while True:
            if callback(item) == False:
                return False

            if not item.HasReference():
                break

            item = item.fundamental_or_item

        return True

    # ---------------------------------------------------------------------------
    def GetFundamentalType(self):
        result = [ None, ]

        # ---------------------------------------------------------------------------
        def Callback(item):
            result[0] = item.fundamental_or_item

        # ---------------------------------------------------------------------------
        
        self.Walk(Callback)
        return result[0]

    # ---------------------------------------------------------------------------
    def ResolveAliases(self):
        result = [ None, ]

        # ---------------------------------------------------------------------------
        def Callback(item):
            result[0] = item
            return item.item_type == ItemType.Alias

        # ---------------------------------------------------------------------------
        
        self.Walk(Callback)

        assert result[0]
        return result[0]

    # ---------------------------------------------------------------------------
    def ResolveAugmentations(self):
        result = [ None, ]

        # ---------------------------------------------------------------------------
        def Callback(item):
            result[0] = item
            return item.item_type in [ ItemType.Alias, ItemType.Augmented, ]

        # ---------------------------------------------------------------------------
        
        self.Walk(Callback)

        assert result[0]
        return result[0]

    # ---------------------------------------------------------------------------
    def GetPotentialMetadata(self, observer):
        assert self._is_committed

        result = self._GetMetadataImpl(observer)

        # If we are looking at an augmented item, combine the metadata
        # of the item and the item that it augments.
        if self.item_type in [ ItemType.Alias, ItemType.Augmented, ] and not self.is_new_type:
            referenced_result = self.fundamental_or_item.GetPotentialMetadata(observer)
            
            for md in itertools.chain(referenced_result.required, referenced_result.optional):
                if not any(md.Name == item.Name for item in itertools.chain(referenced_result.required, referenced_result.optional)):
                    result.optional.append(md)

        return result

    # ---------------------------------------------------------------------------
    def _GetMetadataImpl(self, observer):
        result = QuickObject( required=[],
                              optional=list(UNIVERSAL_METADATA),
                            )

        if self.item_type == ItemType.Compound:
            result.optional.extend(COMPOUND_METADATA)

        if self.arity.max > 1 or self.arity.max == None:
            result.optional.extend(COLLECTION_METADATA)

        return result
