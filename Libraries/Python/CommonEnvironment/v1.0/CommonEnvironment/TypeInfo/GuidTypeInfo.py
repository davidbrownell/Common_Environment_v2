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
# |  Copyright David Brownell 2015.
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
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    @property
    def PythonItemRegularExpressionStrings(self):
        d = { "char" : "[0-9A-Fa-f]", }

        return "({})".format('|'.join([ r"\{%(char)s{32}\}" % d,
                                        r"%(char)s{32}" % d,
                                        r"\{%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}\}" % d,
                                        r"%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % d,
                                      ]))

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