# ---------------------------------------------------------------------------
# |  
# |  DateTimeTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 10:37:55 AM
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
from .DateTypeInfo import DateTypeInfo
from .TimeTypeInfo import TimeTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class DateTimeTypeInfo(FundamentalTypeInfo):
    
    ExpectedType                            = datetime.datetime
    Desc                                    = "Datetime"
    PythonItemRegularExpressionStrings      = "{}.{}".format(DateTypeInfo.PythonItemRegularExpressionStrings[0], TimeTypeInfo.PythonItemRegularExpressionStrings)
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create(microseconds=True):
        result = datetime.datetime.now()

        if not microseconds:
            result = result.replace(microsecond=0)

        return result
        
    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DateTimeTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
