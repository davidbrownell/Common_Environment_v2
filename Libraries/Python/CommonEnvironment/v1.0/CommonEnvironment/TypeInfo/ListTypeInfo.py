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
class ListTypeInfo(TypeInfo.TypeInfo):
    """\
    Useful when itms are lists:

        values = [ [ 1, 2, ], [ 3, 4, 5, ], ... ]
    """

    ExpectedType                            = list
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  element_type_info,
                  **type_info_args
                ):
        super(ListTypeInfo, self).__init__(**type_info_args)
        self.ElementTypeInfo                = element_type_info

    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "ListTypeInfo({super}, element_type_info={element_type_info})" \
                    .format( super=self.PythonDefinitionStringContents,
                             element_type_info=self.ElementTypeInfo.PythonDefinitionString,
                           )

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return self.ElementTypeInfo.ValidateNoThrow(item)
