# ---------------------------------------------------------------------------
# |  
# |  EnumTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/26/2015 09:01:51 PM
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

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class EnumTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (str, unicode)

    # ---------------------------------------------------------------------------
    def __init__( self,
                  values,
                  friendly_values=None,
                  **type_info_args
                ):
        super(EnumTypeInfo, self).__init__(**type_info_args)

        if not values:
            raise Exception("A list of values must be provided")

        if friendly_values != None and len(friendly_values) != len(values):
            raise Exception("The number of friendly_values must match the number of values")

        self.Values                         = values
        self.FriendlyValues                 = friendly_values
    
    # ---------------------------------------------------------------------------
    @property
    def PythonItemRegularExpressionStrings(self):
        return "({})".format('|'.join(self.Values))

    @property
    def ConstraintsDesc(self):
        if len(self.Values) == 1:
            return "Value must be '{}'".format(self.Values[0])

        return "Value must be one of {}".format(', '.join([ "'{}'".format(value) for value in self.Values ]))

    @property
    def PythonDefinitionString(self):
        # ---------------------------------------------------------------------------
        def ListToString(values):
            return "[ {} ]".format(', '.join([ '"{}"'.format(value) for value in values ]))

        # ---------------------------------------------------------------------------
        
        args = OrderedDict()

        if self.FriendlyValues:
            args["friendly_values"] = ListToString(self.FriendlyValues)

        return "EnumTypeInfo({super}, values={values}{args}" \
                    .format( super=self._PythonDefinitionStringContents,
                             values=ListToString(self.Values),
                             args=", ".format(', '.join([ "{}={}".format(k, v) for k, v in args.iteritems() ])) if args else '',
                           )

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if item not in self.Values:
            return "'{}' is not a valid value ({} expected)".format( item,
                                                                     ', '.join([ "'{}'".format(value) for value in self.Values ]),
                                                                   )
