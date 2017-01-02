# ----------------------------------------------------------------------
# |  
# |  GuidTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 19:08:04
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
import uuid

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class GuidTypeInfo(TypeInfo):

    ExpectedType                            = uuid.UUID
    Desc                                    = "Guid"
    ConstraintsDesc                         = ''

    # ----------------------------------------------------------------------
    @staticmethod
    def Create():
        return uuid.uuid4()

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "GuidTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
