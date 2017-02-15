# ----------------------------------------------------------------------
# |  
# |  ObjectLikeTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 20:30:36
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import inflect
import os
import sys

from collections import OrderedDict

from CommonEnvironment.Interface import *

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

Plural = inflect.engine()

# ----------------------------------------------------------------------
class ObjectLikeTypeInfo(TypeInfo):

    # ----------------------------------------------------------------------
    def __init__( self,
                  items=None,               # { "<attribute>" : <TypeInfo>, }
                  require_exact_match=None,

                  # TypeInfo args
                  arity=None,
                  validation_func=None,
                  collection_validation_func=None,

                  **kwargs
                ):
        super(ObjectLikeTypeInfo, self).__init__( arity=arity,
                                                  validation_func=validation_func,
                                                  collection_validation_func=collection_validation_func,
                                                )

        self.Items                          = items or OrderedDict()
        self.RequireExactMatchDefault       = require_exact_match

        for k, v in kwargs.iteritems():
            assert k not in self.Items, k
            self.Items[k] = v

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if not self.Items:
            return ''

        return "Value must contain the {} {}" \
                    .format( Plural.plural("attribute", len(self.Items)),
                             ', '.join([ "'{}'".format(name) for name in self.Items.iterkeys() ]),
                           )

    @property
    def PythonDefinitionString(self):
        return "{}({}, items={}, require_exact_match={})" \
                    .format( self.__class__.__name__,
                             self._PythonDefinitionStringContents,
                             "{{ {} }}".format(', '.join([ '"{}" : {}'.format(k, v.PythonDefinitionString) for k, v in self.Items.iteritems() ])),
                             self.RequireExactMatchDefault,
                           )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl( self,
                                  item, 
                                  recurse=True,
                                  require_exact_match=None,
                                ):
        if require_exact_match == None:
            require_exact_match = self.RequireExactMatchDefault if self.RequireExactMatchDefault != None else True

        if self.Desc == "Class":
            attributes = dir(item)
        elif isinstance(item, dict):
            attributes = item.keys()
        else:
            attributes = item.__dict__.keys()

        attributes = { a for a in attributes if not a.startswith('__') }
    
        for attribute_name, type_info in self.Items.iteritems():
            if attribute_name not in attributes:
                if type_info.Arity.Min == 0:
                    continue

                return "The required attribute '{}' was not found".format(attribute_name)

            attributes.remove(attribute_name)
            
            this_value = self._GetAttributeValue(type_info, item, attribute_name)

            if recurse:
                result = type_info.ValidateNoThrow(this_value)
            else:
                result = type_info.ValidateArityNoThrow(this_value)

            if result != None:
                return "The attribute '{}' is not valid - {}".format(attribute_name, result)

        if require_exact_match and attributes:
            return "The item contains extraneous data: {}".format(', '.join([ "'{}'".format(attr) for attr in attributes ]))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetAttributeValue(type_info, item, attribute_name):
        raise Exception("Abstract method")
