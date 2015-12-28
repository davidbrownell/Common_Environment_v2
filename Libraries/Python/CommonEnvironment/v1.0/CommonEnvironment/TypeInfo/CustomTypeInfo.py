# ---------------------------------------------------------------------------
# |  
# |  CustomTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 12:02:11 PM
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

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

TypeInfo = Package.ImportInit()

# ---------------------------------------------------------------------------
class CustomTypeInfo(TypeInfo.TypeInfo):

    ExpectedTypeIsCallable                  = True

    # ---------------------------------------------------------------------------
    def __init__( self,
                  expected_type_func,       # def Func(item) -> bool
                  validate_item_func,       # def Func(item) -> string on error
                  postprocess_func=None,    # def Func(item) -> item
                  constraints_desc="Custom constraint",
                  **type_info_args
                ):
        super(CustomTypeInfo, self).__init__(**type_info_args)

        self._expected_type_func            = expected_type_func
        self._validate_item_func            = validate_item_func
        self._postprocess_func              = postprocess_func
        self._constraints_desc              = constraints_desc

    # ---------------------------------------------------------------------------
    @property
    def ExpectedType(self, item):
        return self._expected_type_func(item)

    @property
    def ConstraintsDesc(self):
        return self._constraints_desc

    @property
    def PythonDefinitionString(self):
        raise Exception("Python definition strings can't be generated for CustomTypeInfo instances, as it isn't posibile to recreate the associated functions")

    # ---------------------------------------------------------------------------
    def PostprocessItem(self, item):
        return (self._postprocess_func or super(CustomTypeInfo, self).PostprocessItem)(item)

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return self._validate_item_func(item)
