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

from CommonEnvironment.TypeInfo import *

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

                  type_info,
                  default_value=None,       # specific value or def Func(item) -> value
                  
                  # If the following value is True, it is an indication that the presense of this metadata within
                  # a definition indicates that the definition is a new type and not an augmented type. Practically
                  # speaking, this means that the referenced item's metadata will not be copied to the referencing
                  # item as it otherwise would.
                  is_new_type=False,
                ):
        self.Name                           = name
        self.TypeInfo                       = type_info
        self.DefaultValue                   = default_value
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
UNIVERSAL_METADATA = [ Metadata("description", StringTypeInfo(min_length=0), default_value=''),
                     ]

COMPOUND_METADATA = [ Metadata("polymorphic", BoolTypeInfo(), default_value=False),
                      
                      # Compound elements that are based on polymorphic elements will also 
                      # be polymorphic unless this value is explicitly set.
                      Metadata("suppress_polymorphic", BoolTypeInfo(), default_value=False),

                      Metadata("define", BoolTypeInfo(), default_value=True),
                    ]

COLLECTION_METADATA = [ Metadata("plural", StringTypeInfo(), default_value=lambda item: pluralize.plural(item.name) if item.name else None),
                      ]
                      
OPTIONAL_METADATA = [ Metadata("default", StringTypeInfo()),
                    ]

# ---------------------------------------------------------------------------
# |  Fundamental Types
STRING_METADATA = ( [],
                    [ Metadata("validation", StringTypeInfo()),
                      Metadata("min_length", IntTypeInfo(min=0)),
                      Metadata("max_length", IntTypeInfo(min=1)),
                    ]
                  )

ENUM_METADATA = ( [ Metadata("values", StringTypeInfo(arity='+')),
                  ],
                  [ Metadata("friendly_values", StringTypeInfo(arity='+')),
                  ]
                )

INTEGER_METADATA = ( [],
                     [ Metadata("min", IntTypeInfo()),
                       Metadata("max", IntTypeInfo()),
                       Metadata("bytes", IntTypeInfo(validation_func=lambda value: "'{}' must be {}".format(value, ', '.join([ str(v) for v in [ 1, 2, 4, 8, ] ])) if value not in [ 1, 2, 4, 8, ] else None)),
                     ]
                   )
                  
NUMBER_METADATA = ( [],
                    [ Metadata("min", FloatTypeInfo()),
                      Metadata("max", FloatTypeInfo()),
                    ]
                  )

FILENAME_METADATA = ( [],
                      [ Metadata("type", EnumTypeInfo([ "file", "directory", "either", ])),
                        Metadata("must_exist", BoolTypeInfo()),
                      ]
                    )

CUSTOM_METADATA = ( [ Metadata("type", StringTypeInfo()),
                    ],
                    []
                  )
