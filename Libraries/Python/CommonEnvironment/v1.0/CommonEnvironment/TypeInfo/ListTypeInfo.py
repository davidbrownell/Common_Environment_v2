# ---------------------------------------------------------------------------
# |  
# |  ListTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 11:50:29 AM
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

from CommonEnvironment import TypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class ListTypeInfo(TypeInfo.TypeInfo):
    """\
    Useful when itms are lists:

        values = [ [ 1, 2, ], [ 3, 4, 5, ], ... ]
    """

    ExpectedType                            = list
    Desc                                    = "List"
    
    # ---------------------------------------------------------------------------
    def __init__( self, 
                  element_type_info,
                  **type_info_args
                ):
        super(ListTypeInfo, self).__init__(**type_info_args)
        self.ElementTypeInfo                = element_type_info

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return "List of items where: {}".format(self.ElementTypeInfo.ConstraintsDesc)

    @property
    def PythonDefinitionString(self):
        return "ListTypeInfo({super}, element_type_info={element_type_info})" \
                    .format( super=self._PythonDefinitionStringContents,    # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                             element_type_info=self.ElementTypeInfo.PythonDefinitionString,
                           )

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item
        
    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return self.ElementTypeInfo.ValidateNoThrow(item)
