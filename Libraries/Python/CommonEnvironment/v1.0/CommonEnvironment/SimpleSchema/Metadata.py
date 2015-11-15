# ---------------------------------------------------------------------------
# |  
# |  Metadata.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/06/2015 07:09:39 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inflect
import os
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

pluralize = inflect.engine()

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Metadata(object):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  name,
                  type,
                  default_value=None,       # specific value or def Func(item) -> value
                  supported_values=None,

                  # If the following value is True, it is an indication that the presense of this metadata within
                  # a definition indicates that the definition is a new type and not an augmented type. Practically
                  # speaking, this means that the referenced item's metadata will not be copied to the referencing
                  # item as it otherwise would.
                  is_new_type=False,
                ):
        self.Name                           = name
        self.Type                           = type
        self.DefaultValue                   = default_value
        self.SuportedValues                 = supported_values
        self.IsNewType                      = is_new_type

        self.IsDynamicDefaultValue          = callable(self.DefaultValue)

    # ---------------------------------------------------------------------------
    def ApplyDefault(self, item):
        assert self.DefaultValue != None

        if self.IsDynamicDefaultValue:
            return self.DefaultValue(item)

        return self.DefaultValue

# ---------------------------------------------------------------------------
# |
# |  Public Data
# |
# ---------------------------------------------------------------------------
UNIVERSAL_METADATA = [ Metadata("description", str, default_value=''),
                     ]

COMPOUND_METADATA = [ Metadata("polymorphic", bool, default_value=False),
                      # Compound elements without children that are based on polymorphic
                      # elements will also be polymorphic unless this value is explicitly
                      # set.
                      Metadata("suppress_polymorphic", bool, default_value=False),

                      # Note that 'polymorphic_base' will be set to True for a root 
                      # polymorphic object.
                    ]

COLLECTION_METADATA = [ Metadata("plural", str, default_value=lambda item: pluralize.plural(item.Name) if item.Name else None),
                      ]
