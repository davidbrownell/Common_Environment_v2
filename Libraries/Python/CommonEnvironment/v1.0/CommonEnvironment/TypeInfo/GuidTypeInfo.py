# ---------------------------------------------------------------------------
# |  
# |  GuidTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 10:26:19 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import uuid

from .Impl.FundamentalTypeInfo import FundamentalTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class GuidTypeInfo(FundamentalTypeInfo):
    
    ExpectedType                            = uuid.UUID
    Desc                                    = "Guid"
    ConstraintsDesc                         = ''

    _d = { "char" : "[0-9A-Fa-f]", }

    PythonItemRegularExpressionInfo         = [ r"\{%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}\}" % _d,
                                                r"%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % _d,
                                                r"\{%(char)s{32}\}" % _d,
                                                r"%(char)s{32}" % _d,
                                              ]

    del _d

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return uuid.uuid4()
        
    @property
    def PythonDefinitionString(self):
        return "GuidTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
