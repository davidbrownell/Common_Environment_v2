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