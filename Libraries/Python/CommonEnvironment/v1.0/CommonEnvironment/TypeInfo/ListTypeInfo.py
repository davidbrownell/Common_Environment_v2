# ----------------------------------------------------------------------
# |  
# |  ListTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 07:54:11
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
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
class ListTypeInfo(TypeInfo):
    """\
    Useful when items are lists:

        values = [ [ 1, 2, ], [ 3, 4, 5, ], ... ]
    """

    ExpectedType                            = list
    Desc                                    = "List"

    # ----------------------------------------------------------------------
    def __init__( self,
                  element_type_info,
                  **type_info_args
                ):
        super(ListTypeInfo, self).__init__(**type_info_args)

        self.ElementTypeInfo                = element_type_info

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return "List of '{}' items where: {}".format(self.ElementTypeInfo.Desc, self.ElementTypeInfo.ConstraintsDesc)

    @property
    def PythonDefinitionString(self):
        return "ListTypeInfo({}, element_type_info={})" \
                    .format( self._PythonDefinitionStringContents,
                             self.ElementTypeInfo.PythonDefinitionString,
                           )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return self.ElementTypeInfo.ValidateNoThrow(item)
