# ---------------------------------------------------------------------------
# |  
# |  FloatTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/26/2015 10:03:41 PM
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

from collections import OrderedDict

from .Impl.FundamentalTypeInfo import FundamentalTypeInfo
from .IntTypeInfo import IntTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class FloatTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (float, int)
    Desc                                    = "Float"

    # ---------------------------------------------------------------------------
    def __init__( self,
                  min=None,
                  max=None,
                  **type_info_args
                ):
        super(FloatTypeInfo, self).__init__(**type_info_args)

        if min != None and max != None and max < min:
            raise Exception("Invalid argument - max")

        self.Min                            = min
        self.Max                            = max

    # ---------------------------------------------------------------------------
    @property
    def PythonItemRegularExpressionStrings(self):
        return r"{}\.[0-9]+".format(IntTypeInfo.PythonItemRegularExpressionStringsImpl(self.Min, self.Max))

    @property
    def ConstraintsDesc(self):
        items = []

        if self.Min != None:
            items.append("be >= {}".format(self.Min))

        if self.Max != None:
            items.append("be <= {}".format(self.Max))

        if not items:
            return ''

        return "Value must {}".format(', '.join(items))

    @property
    def PythonDefinitionString(self):
        args = OrderedDict()

        if self.Min != None:
            args["min"] = self.Min

        if self.Max != None:
            args["max"] = self.Max

        return "FloatTypeInfo({super}{args})" \
                    .format( super=self._PythonDefinitionStringContents,
                             args=', '.join(', '.join([ "{}={}".format(k, v) for k, v in args.iteritems() ])),
                           )

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if self.Min != None and item < self.Min:
            return "{} is not >= {}".format(item, self.Min)

        if self.Max != None and item > self.Max:
            return "{} is not <= {}".format(item, self.Max)
