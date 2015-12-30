# ---------------------------------------------------------------------------
# |  
# |  DurationTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 10:58:07 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
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

class DurationTypeInfo(FundamentalTypeInfo):
    
    ExpectedType                            = datetime.timedelta
    Desc                                    = "Duration"
    PythonItemRegularExpressionStrings      = r"([1-9][0-9]*|0)?:[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?"
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DurationTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
