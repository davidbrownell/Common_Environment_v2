# ---------------------------------------------------------------------------
# |  
# |  ClassTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 11:41:06 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inspect
import os
import sys

from collections import namedtuple

from . import TypeInfo
from .Impl.ObjectLikeTypeInfo import ObjectLikeTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
class _MethodTypeInfo(TypeInfo):
    ExpectedTypeIsCallable                  = True
    ConstraintsDesc                         = ''

    # ---------------------------------------------------------------------------
    def __init__(self):
        super(_MethodTypeInfo, self).__init__( arity=None,
                                               validation_func=None,
                                             )

    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "{name}({super})" \
                    .format( name=self.__class__.__name__,
                             super=self._PythonDefinitionStringContents, # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                           )

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(item):
        return

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
class MethodTypeInfo(_MethodTypeInfo):
    Desc                                    = "Method"
    ExpectedType                            = staticmethod(lambda item: inspect.ismethod(item) and item.__self__ == None)

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
class ClassMethodTypeInfo(_MethodTypeInfo):
    Desc                                    = "Class Method"
    ExpectedType                            = staticmethod(lambda item: inspect.ismethod(item) and item.__self__ != None)

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
class StaticMethodTypeInfo(_MethodTypeInfo):
    Desc                                    = "Static Method"
    ExpectedType                            = staticmethod(inspect.isfunction)

# ---------------------------------------------------------------------------
class ClassTypeInfo(ObjectLikeTypeInfo):

    # ---------------------------------------------------------------------------
    # |  Public Properties
    ExpectedType                            = staticmethod(lambda item: True) # Everything is a class in Python
    ExpectedTypeIsCallable                  = True
    Desc                                    = "Class"

    # ---------------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    def _HasAttribute(item, attribute_name):
        return hasattr(item, attribute_name)

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetAttributeValue(cls, type_info, item, attribute_name):
        if isinstance(type_info, _MethodTypeInfo):
            item = type(item)

        return getattr(item, attribute_name)
