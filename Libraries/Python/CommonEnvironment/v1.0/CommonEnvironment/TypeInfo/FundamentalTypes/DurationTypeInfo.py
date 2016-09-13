# ----------------------------------------------------------------------
# |  
# |  DurationTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 18:49:39
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
import os
import sys

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class DurationTypeInfo(TypeInfo):

    ExpectedType                            = datetime.timedelta
    Desc                                    = "Duration"
    ConstraintsDesc                         = ''

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DurationTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
