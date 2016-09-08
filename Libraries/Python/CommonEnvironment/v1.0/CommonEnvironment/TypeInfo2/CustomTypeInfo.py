# ----------------------------------------------------------------------
# |  
# |  CustomTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 07:47:49
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from . import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class CustomTypeInfo(TypeInfo):

    Desc                                    = "Custom Type"

    # ----------------------------------------------------------------------
    def __init__( self,
                  expected_type_func,                   # def Func(item) -> bool
                  validate_item_func,                   # def Func(item) -> string on error
                  constraints_desc="Custom constraint",
                  **type_info_args
                ):
        super(CustomTypeInfo, self).__init__(**type_info_args)

        self._expected_type_func            = expected_type_func
        self._validate_item_func            = validate_item_func
        self._constraints_desc              = constraints_desc

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return self._constraints_desc

    @property
    def PythonDefinitionString(self):
        raise Exception("Python definition strings can't be generated for CustomTypeInfo instances, as it isn't posibile to recreate the associated functions")

    # ----------------------------------------------------------------------
    def ExpectedType(self, item):
        return self._expected_type_func(item)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _ExpectedTypeIsCallable                 = True

    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        return self._validate_item_func(item)
