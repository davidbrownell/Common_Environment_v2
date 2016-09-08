# ----------------------------------------------------------------------
# |  
# |  AnyOfTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 20:17:37
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
class AnyOfTypeInfo(TypeInfo):

    # ----------------------------------------------------------------------
    def __init__( self,
                  type_info_list,
                  **type_info_args
                ):
        super(AnyOfTypeInfo, self).__init__(**type_info_args)

        self.ElementTypeInfos               = type_info_list

    # ----------------------------------------------------------------------
    @property
    def Desc(self):
        return "Any of {}".format(', '.join([ "'{}'".format(eti.Desc) for eti in self.ElementTypeInfos ]))

    @property
    def ConstraintsDesc(self):
        items = []

        for eti in self.ElementTypeInfos:
            constraint_desc = eti.ConstraintsDesc
            if constraint_desc:
                items.append("{}: {}".format(eti.Desc, constraint_desc))

        return "Value where: {}".format(' / '.join(items))

    @property
    def PythonDefinitionString(self):
        return "AnyOfTypeInfo({}, type_info_list={})" \
                    .format( self._PythonDefinitionStringContents,
                             "[ {} ]".format(', '.join([ eti.PythonDefinitionString for eti in self.ElementTypeInfos ])),
                           )

    # ----------------------------------------------------------------------
    def ExpectedType(self, item):
        return bool(self._GetElementTypeInfo(item))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _ExpectedTypeIsCallable                 = True

    # ----------------------------------------------------------------------
    def _GetElementTypeInfo(self, item):
        for eti in self.ElementTypeInfos:
            if eti.IsExpectedType(item):
                return eti

    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        eti = self._GetElementTypeInfo(item)
        assert eti

        return eti.ValidateItemNoThrow(item, **custom_args)
