# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/06/2015 01:55:15 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class ModifiableValue(object):
    def __init__(self, value):
        self.value                          = value

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Get( items, 
         functor,                           # def Func(item) -> Bool
         extractor=None,                    # def Func(item) -> Any
       ):
    for item in items:
        if functor(item):
            return extractor(item) if extractor else item

# ----------------------------------------------------------------------
def GetIndex( items,
              functor,                      # def Func(item) -> Bool
            ):
    for index, item in enumerate(items):
        if functor(item):
            return index

# ---------------------------------------------------------------------------
def All( items,
         functor,                           # def Func(item) -> Bool
       ):
    for item in items:
        if not functor(item):
            return False

    return bool(items)

# ---------------------------------------------------------------------------
def Any( items,
         functor,                           # def Func(item) -> Bool
       ):
    for item in items:
        if functor(item):
            return True

    return False

# ----------------------------------------------------------------------
def ToPascalCase(s):
    """Returns APascalCase string"""
    parts = s.split('_')

    # Handle corner case where the original string starts or ends with an underscore
    if not parts[0]:
        parts[0] = '_'

    if len(parts) > 1 and not parts[-1]:
        parts[-1] = '_'

    return ''.join([ "{}{}".format(part[0].upper(), part[1:]) for part in parts ])

# ----------------------------------------------------------------------
_ToSnakeCase_regex = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")
    
def ToSnakeCase(s):
    """Returns a_snake_case string"""
    return _ToSnakeCase_regex.sub(r'_\1', s).lower().replace('__', '_')

    
