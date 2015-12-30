# ---------------------------------------------------------------------------
# |  
# |  ObjectLikeTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 11:13:18 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inflect
import os
import sys

from collections import OrderedDict

from CommonEnvironment.Interface import *

from .. import TypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

Plural = inflect.engine()

# ---------------------------------------------------------------------------
class ObjectLikeTypeInfo(TypeInfo):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  items=None,               # { "<attribute>" : <TypeInfo>, }
                  require_exact_match=False,
                  arity=None,
                  validation_func=None,
                  **kwargs
                ):
        super(ObjectLikeTypeInfo, self).__init__( arity=arity,
                                                  validation_func=validation_func,
                                                )

        self.RequireExactMatch              = require_exact_match
        self.Items                          = items or OrderedDict()

        for k, v in kwargs.iteritems():
            assert k not in self.Items, k
            self.Items[k] = v

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if not self.Items:
            return ''

        return "Value must {only}contain the {attribute} {values}" \
                    .format( only="only " if self.RequireExactMatch else '',
                             attribute=Plural.plural("attribute", len(self.Items)),
                             values=', '.join([ "'{}'".format(name) for name in self.Items.iterkeys() ]),
                           )

    @property
    def PythonDefinitionString(self):
        return "{name}({super}, items={items}, require_exact_match={require_exact_match})" \
                    .format( name=self.__class__.__name__,
                             super=self._PythonDefinitionStringContents,
                             items="{ %s }" % ', '.join([ '"{}" : {}'.format(k, v.PythonDefinitionString) for k, v in self.Items.iteritems() ]),
                             require_exact_match=self.RequireExactMatch,
                           )

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if self.RequireExactMatch:
            attributes = { a for a in item.__dict__.keys() if not a.startswith("__") }

            # ---------------------------------------------------------------------------
            def ProcessAttribte(attr):
                attributes.remove(attr)

            # ---------------------------------------------------------------------------
            def OnComplete():
                if attributes:
                    return "The item contained extraneous data: {}".format(', '.join([ "'{}'".format(attr) for attr in attributes ]))

            # ---------------------------------------------------------------------------
            
        else:
            ProcessAttribute = lambda attr: None
            OnComplete = lambda: None
            
        for attribute_name, type_info in self.Items.iteritems():
            ProcessAttribute(attribute_name)
            
            if not self._HasAttribute(item, attribute_name):
                return "The attribute '{}' was not found".format(attribute_name)

            this_value = self._GetAttributeValue(type_info, item, attribute_name)

            result = type_info.ValidateNoThrow(this_value)
            if result != None:
                return "The attribute '{}' is not valid - {}".format(attribute_name, result)

        result = OnComplete()
        if result != None:
            return result

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _HasAttribute(item, attribute_name):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetAttributeValue(type_info, item, attribute_name):
        raise Exception("Abstract method")

    

