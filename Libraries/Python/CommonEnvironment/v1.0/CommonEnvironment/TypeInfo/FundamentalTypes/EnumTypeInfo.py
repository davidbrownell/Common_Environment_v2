# ----------------------------------------------------------------------
# |  
# |  EnumTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 18:51:59
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class EnumTypeInfo(TypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "Enum"

    # ----------------------------------------------------------------------
    def __init__( self,
                  values,
                  friendly_values=None,
                  **type_info_args
                ):
        super(EnumTypeInfo, self).__init__(**type_info_args)

        if not values:
            raise Exception("A list of values must be provided")

        if friendly_values != None and len(friendly_values) != len(values):
            raise Exception("The number of 'friendly_values' must match the number of 'values'")

        self.Values                         = values
        self.FriendlyValues                 = friendly_values

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if len(self.Values) == 1:
            return 'Value must be "{}"'.format(self.Values[0])

        return "Value must be one of {}".format(', '.join([ '"{}"'.format(value) for value in self.Values ]))

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        # ----------------------------------------------------------------------
        def ListToString(values):
            return "[ {} ]".format(', '.join([ '"{}"'.format(value) for value in values ]))

        # ----------------------------------------------------------------------
        
        return "EnumTypeInfo({}, values={}{})" \
                    .format( self._PythonDefinitionStringContents,
                             ListToString(self.Values),
                             '' if not self.FriendlyValues else ", friendly_values={}".format(ListToString(self.FriendlyValues)),
                           )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if item not in self.Values:
            return "'{}' is not a valid value ({} expected)".format( item,
                                                                     ', '.join([ "'{}'".format(value) for value in self.Values ]),
                                                                   )
