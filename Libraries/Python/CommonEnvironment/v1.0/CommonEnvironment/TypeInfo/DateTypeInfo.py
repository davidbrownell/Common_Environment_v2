# ---------------------------------------------------------------------------
# |  
# |  DateTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 10:47:23 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import os
import sys

from .Impl.FundamentalTypeInfo import FundamentalTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class DateTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = datetime.date
    Desc                                    = "Date"
    PythonItemRegularExpressionStrings      = r"[0-9]{4}-(0?[1-9]|1[0-2])-([0-2][0-9]|3[0-1])"
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.date.today()
        
    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DateTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
