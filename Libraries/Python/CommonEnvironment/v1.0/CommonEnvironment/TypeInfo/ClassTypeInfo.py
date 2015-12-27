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
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inspect
import os
import sys

from CommonEnvironment import Package

from .Impl.ObjectLikeTypeInfo import ObjectLikeTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

TypeInfo = Package.ImportInit()

# ---------------------------------------------------------------------------
class ClassTypeInfo(ObjectLikeTypeInfo):

    # ---------------------------------------------------------------------------
    # |  Public Types
    class _MethodTypeInfo(TypeInfo.TypeInfo):
        ExpectedTypeIsCallable              = True
        ConstraintsDesc                     = ''

        def __init__(self):
            super(ClassTypeInfo._MethodTypeInfo, self).__init__( arity=None,
                                                                 validation_func=None,
                                                               )

        @property
        def PythonDefinitionString(self):
            return "ClassTypeInfo.{name}({super})" \
                        .format( name=self.__class__.__name__,
                                 super=self.PythonDefinitionStringContents,
                               )

        @staticmethod
        def _ValidateItemNoThrowImpl(item):
            return

    # ---------------------------------------------------------------------------
    class MethodTypeInfo(_MethodTypeInfo):
        ExpectedType                        = staticmethod(lambda item: inspect.ismethod(item) and item.__self__ == None)

    # ---------------------------------------------------------------------------
    class ClassMethodTypeInfo(_MethodTypeInfo):
        ExpectedType                        = staticmethod(lambda item: inspect.ismethod(item) and item.__self__ != None)

    # ---------------------------------------------------------------------------
    class StaticMethodTypeInfo(_MethodTypeInfo):
        ExpectedType                        = staticmethod(lambda item: inspect.isfunction(dict_items))

    # ---------------------------------------------------------------------------
    # |  Public Properties
    ExpectedType                            = staticmethod(lambda item: True) # Everything is a class in Python
    ExpectedTypeIsCallable                  = True

    # ---------------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    def _HasAttribute(item, attribute_name):
        return hasattr(item, attribute_name)

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetAttributeValue(cls, type_info, item, attribute_name):
        if isinstance(type_info, cls._MethodTypeInfo):
            item = type(item)

        return getattr(item, attribute_name)

    
    