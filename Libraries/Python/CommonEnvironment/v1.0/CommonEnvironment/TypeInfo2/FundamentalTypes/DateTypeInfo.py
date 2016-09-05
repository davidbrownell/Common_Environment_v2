# ----------------------------------------------------------------------
# |  
# |  DateTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 18:40:30
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
class DateTypeInfo(TypeInfo):

    ExpectedType                            = datetime.date
    Desc                                    = "Date"
    ConstraintsDesc                         = ''

    # ----------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.date.today()

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DateTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
    