# ----------------------------------------------------------------------
# |  
# |  IntTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 19:10:24
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from collections import OrderedDict

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class IntTypeInfo(TypeInfo):

    ExpectedType                            = int
    Desc                                    = "Integer"

    # ----------------------------------------------------------------------
    def __init__( self,
                  min=None,
                  max=None,
                  bytes=None,
                  **type_info_args
                ):
        super(IntTypeInfo, self).__init__(**type_info_args)

        if min != None and max != None and max < min:
            raise Exception("Invalid argument - 'max'")

        is_byte_default = False
        
        if bytes:
            if bytes not in [ 1, 2, 4, 8, ]:
                raise Exception("Invalid argument - 'bytes'")
            
            range_min = 0
            range_max = (1 << (bytes * 8)) - 1

            if min == None or min < 0:
                half = range_max / 2
                
                range_min = -(half + 1)
                range_max = half

            if min != None:
                if min < range_min:
                    raise Exception("Invalid argument - 'bytes' and 'min'")
            else:
                min = range_min
            
            if max != None:
                if max > range_max:
                    raise Exception("Invalid argument - 'bytes' and 'max'")
            else:
                max = range_max
                
            is_byte_default = min == range_min and max == range_max
            
        self.Min                            = min
        self.Max                            = max
        self.Bytes                          = bytes
        self.IsByteDefault                  = is_byte_default
        
    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        args = OrderedDict()

        if self.Min != None and not self.IsByteDefault:
            args["min"] = self.Min

        if self.Max != None and not self.IsByteDefault:
            args["max"] = self.Max

        if self.Bytes != None:
            args["bytes"] = self.Bytes

        return "IntTypeInfo({}{})" \
                    .format( self._PythonDefinitionStringContents,
                             '' if not args else ", {}".format(', '.join([ "{}={}".format(k, v) for k, v in args.iteritems() ])),
                           )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if self.Min != None and item < self.Min:
            return "{} is not >= {}".format(item, self.Min)

        if self.Max != None and item > self.Max:
            return "{} is not <= {}".format(item, self.Max)
