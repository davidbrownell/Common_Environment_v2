# ---------------------------------------------------------------------------
# |  
# |  TimeTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 10:51:50 AM
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

class TimeTypeInfo(FundamentalTypeInfo):
    
    ExpectedType                            = datetime.time
    Desc                                    = "Time"
    PythonItemRegularExpressionStrings      = r"([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(\+[0-9]+:[0-9]+)?"
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.datetime.now().time()
        
    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "TimeTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
