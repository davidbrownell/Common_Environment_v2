# ---------------------------------------------------------------------------
# |  
# |  AnyOfTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 11:54:45 AM
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
class AnyOfTypeInfo(TypeInfo.TypeInfo):

    ExpectedTypeIsCallable                  = True
    
    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info_list,
                  **type_info_args
                ):
        super(AnyOfTypeInfo, self).__init__(**type_info_args)
        self.ElementTypeInfos               = type_info_list

    # ---------------------------------------------------------------------------
    @property
    def ExpectedType(self, item):
        for eti in self.ElementTypeInfos:
            if callable(eti.ExpectedType):
                if eti.ExpectedType(item):
                    return True
            else:
                if isinstance(item, eti.ExpectedType):
                    return True

    @property
    def Desc(self):
        return "Any of {}".format(', '.join([ "'{}'".format(eti.Desc) for eti in self.ElementTypeInfos ]))

    @property
    def ConstraintsDesc(self):
        items = []

        for eti in self.ElementTypeInfos:
            constraint_desc = eti.ConstraintDesc
            if constraint_desc:
                items.append("{}: {}".format(eti.Desc, constraint_desc))

        return '/'.join(items)

    @property
    def PythonDefinitionString(self):
        return "AnyOfTypeInfo({super}, type_info_list={type_info_list})" \
                    .format( super=self._PythonDefinitionStringContents,
                             type_info_list="[ {} ]".format(', '.join([ eti.PythonDefinitionString for eti in self.ElementTypeInfos ])),
                           )

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        for eti in self.ElementTypeInfos:
            result = eti.ValidateItemNoThrow(item)
            if item == None:
                return

        return "'{}' could not be validated".format(item)
                         