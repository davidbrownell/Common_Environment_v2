# ----------------------------------------------------------------------
# |  
# |  ClassTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 20:29:59
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import inspect
import os
import sys

from CommonEnvironment import Interface

from . import TypeInfo
from .Impl.ObjectLikeTypeInfo import ObjectLikeTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class _MethodTypeInfo(TypeInfo):

    ConstraintsDesc                         = ''

    # ----------------------------------------------------------------------
    def __init__(self):
        super(_MethodTypeInfo, self).__init__()

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "{}({})" \
                    .format( self.__class__.__name__,
                             self._PythonDefinitionStringContents,
                           )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _ExpectedTypeIsCallable                 = True

    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        return

# ----------------------------------------------------------------------
class MethodTypeInfo(_MethodTypeInfo):
    Desc                                    = "Method"
    ExpectedType                            = staticmethod(Interface.IsStandardMethod)

# ----------------------------------------------------------------------
class ClassMethodTypeInfo(_MethodTypeInfo):
    Desc                                    = "Class Method"
    ExpectedType                            = staticmethod(Interface.IsClassMethod)

# ----------------------------------------------------------------------
class StaticMethodTypeInfo(_MethodTypeInfo):
    Desc                                    = "Static Method"
    ExpectedType                            = staticmethod(Interface.IsStaticMethod)

# ----------------------------------------------------------------------
@Interface.staticderived
class ClassTypeInfo(ObjectLikeTypeInfo):

    Desc                                    = "Class"
    ExpectedType                            = staticmethod(lambda item: True) # Everything is an object in Python
    
    # ----------------------------------------------------------------------
    @classmethod
    def _GetAttributeValue(cls, type_info, item, attribute_name):
        if isinstance(type_info, _MethodTypeInfo):
            item = type(item)

        return getattr(item, attribute_name)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _ExpectedTypeIsCallable                 = True
