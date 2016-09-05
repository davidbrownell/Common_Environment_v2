# ----------------------------------------------------------------------
# |  
# |  StringTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 19:18:48
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import inflect
import os
import re
import sys

from collections import OrderedDict

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

Plural = inflect.engine()

# ----------------------------------------------------------------------
class StringTypeInfo(TypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "String"

    # ----------------------------------------------------------------------
    def __init__( self,
                  validation_expression=None,
                  min_length=None,
                  max_length=None,
                  **type_info_args
                ):
        super(StringTypeInfo, self).__init__(**type_info_args)

        if validation_expression:
            if min_length != None or max_length != None:
                raise Exception("'min_length' and 'max_length' should not be provided when 'validation_expression' is provided")
        elif min_length == None:
            min_length = 1

        if min_length != None and max_length != None and max_length < min_length:
            raise Exception("Invalid argument - 'max_length'")

        self.ValidationExpression           = validation_expression
        self.MinLength                      = min_length
        self.MaxLength                      = max_length

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        items = []

        if self.ValidationExpression:
            items.append("match the regular expression '{}'".format(self.ValidationExpression))

        if self.MinLength:
            items.append("have more than {}".format(Plural.no("character", self.MinLength)))

        if self.MaxLength:
            items.append("have less than {}".format(Plural.no("character", self.MaxLength)))

        if not items:
            return ''

        return "Value must {}".format(', '.join(items))

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        args = OrderedDict()

        if self.ValidationExpression:
            args["validation_expression"] = 'r"{}"'.format(self.ValidationExpression)

        if self.MinLength != None:
            args["min_length"] = self.MinLength

        if self.MaxLength != None:
            args["max_length"] = self.MaxLength

        return "StringTypeInfo({}{})" \
                    .format( self._PythonDefinitionStringContents,
                             '' if not args else ", {}".format(', '.join([ "{}={}".format(k, v) for k, v in args.iteritems() ])),
                           )

    # ----------------------------------------------------------------------
    def __getstate__(self):
        # Help with pickling, as it isn't possible to pickle a dynamic function
        d = dict(self.__dict__)

        if "_DynamicValidate" in d:
            del d["_DynamicValidate"]

        return d

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if not hasattr(self, "_DynamicValidate"):
            if self.ValidationExpression:
                regex = re.compile(self.ValidationExpression)
                self._DynamicValidate = regex.match
            else:
                self._DynamicValidate = lambda i: True

        if not self._DynamicValidate(item):
            return "'{}' did not match the validation expression '{}'".format(item, self.ValidationExpression)

        item_length = len(item)

        if self.MinLength != None and item_length < self.MinLength:
            return "{} found in the item '{}' (At least {} expected)".format( Plural.no("character", item_length),
                                                                              item,
                                                                              Plural.no("character", self.MinLength),
                                                                            )

        if self.MaxLength != None and item_length > self.MaxLength:
            return "{} found in the item '{}' (At most {} expected)".format( Plural.no("character", item_length),
                                                                             item,
                                                                             Plural.no("character", self.MaxLength),
                                                                           )
