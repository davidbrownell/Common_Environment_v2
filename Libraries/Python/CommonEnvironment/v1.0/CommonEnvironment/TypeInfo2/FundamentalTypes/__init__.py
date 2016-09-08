# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 18:11:17
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

from CommonEnvironment import Interface as _Interface

# If we are importing as part of a unit test, we don't want to include
# these files as it will lead to circular dependencies. A normal import
# will have already include the base modules, meaning there were be '.'s 
# in the __name__.
#
# This is required because this is a __init__ file that is importing sibling
# files into its own namespace. This practice is generally frowned upon, but 
# useful is this particular scenario.

if '.' in __name__:
    from .BoolTypeInfo import BoolTypeInfo
    from .DateTimeTypeInfo import DateTimeTypeInfo
    from .DateTypeInfo import DateTypeInfo
    from .DirectoryTypeInfo import DirectoryTypeInfo
    from .DurationTypeInfo import DurationTypeInfo
    from .EnumTypeInfo import EnumTypeInfo
    from .FilenameTypeInfo import FilenameTypeInfo
    from .FloatTypeInfo import FloatTypeInfo
    from .GuidTypeInfo import GuidTypeInfo
    from .IntTypeInfo import IntTypeInfo
    from .StringTypeInfo import StringTypeInfo
    from .TimeTypeInfo import TimeTypeInfo
    
    from .. import Arity

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Visitor(_Interface.Interface):

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnBool(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDateTime(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDate(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDirectory(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDuration(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnEnum(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnFilename(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnFloat(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnGuid(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnInt(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnString(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnTime(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, type_info, *args, **kwargs):
        if isinstance(type_info, BoolTypeInfo):
            return cls.OnBool(type_info, *args, **kwargs)
        elif isinstance(type_info, DateTimeTypeInfo):
            return cls.OnDateTime(type_info, *args, **kwargs)
        elif isinstance(type_info, DateTypeInfo):
            return cls.OnDate(type_info, *args, **kwargs)
        elif isinstance(type_info, DirectoryTypeInfo):
            return cls.OnDirectory(type_info, *args, **kwargs)
        elif isinstance(type_info, DurationTypeInfo):
            return cls.OnDuration(type_info, *args, **kwargs)
        elif isinstance(type_info, EnumTypeInfo):
            return cls.OnEnum(type_info, *args, **kwargs)
        elif isinstance(type_info, FilenameTypeInfo):
            return cls.OnFilename(type_info, *args, **kwargs)
        elif isinstance(type_info, FloatTypeInfo):
            return cls.OnFloat(type_info, *args, **kwargs)
        elif isinstance(type_info, GuidTypeInfo):
            return cls.OnGuid(type_info, *args, **kwargs)
        elif isinstance(type_info, IntTypeInfo):
            return cls.OnInt(type_info, *args, **kwargs)
        elif isinstance(type_info, StringTypeInfo):
            return cls.OnString(type_info, *args, **kwargs)
        elif isinstance(type_info, TimeTypeInfo):
            return cls.OnTime(type_info, *args, **kwargs)
        else:
            raise Exception("'{}' was not expected".format(type(type_info)))

# ----------------------------------------------------------------------
class SimpleVisitor(Visitor):
    # ----------------------------------------------------------------------
    def __init__( self,
                  onBoolFunc=None,          # def Func(type_info, *args, **kwargs)
                  onDateTimeFunc=None,      # def Func(type_info, *args, **kwargs)
                  onDateFunc=None,          # def Func(type_info, *args, **kwargs)
                  onDirectoryFunc=None,     # def Func(type_info, *args, **kwargs)
                  onDurationFunc=None,      # def Func(type_info, *args, **kwargs)
                  onEnumFunc=None,          # def Func(type_info, *args, **kwargs)
                  onFilenameFunc=None,      # def Func(type_info, *args, **kwargs)
                  onFloatFunc=None,         # def Func(type_info, *args, **kwargs)
                  onGuidFunc=None,          # def Func(type_info, *args, **kwargs)
                  onIntFunc=None,           # def Func(type_info, *args, **kwargs)
                  onStringFunc=None,        # def Func(type_info, *args, **kwargs)
                  onTimeFunc=None,          # def Func(type_info, *args, **kwargs)
                ):
        self._onBoolFunc                    = onBoolFunc or self._Empty
        self._onDateTimeFunc                = onDateTimeFunc or self._Empty
        self._onDateFunc                    = onDateFunc or self._Empty
        self._onDirectoryFunc               = onDirectoryFunc or self._Empty
        self._onDurationFunc                = onDurationFunc or self._Empty
        self._onEnumFunc                    = onEnumFunc or self._Empty
        self._onFilenameFunc                = onFilenameFunc or self._Empty
        self._onFloatFunc                   = onFloatFunc or self._Empty
        self._onGuidFunc                    = onGuidFunc or self._Empty
        self._onIntFunc                     = onIntFunc or self._Empty
        self._onStringFunc                  = onStringFunc or self._Empty
        self._onTimeFunc                    = onTimeFunc or self._Empty

    # ----------------------------------------------------------------------
    def OnBool(self, type_info, *args, **kwargs):
        return self._onBoolFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnDateTime(self, type_info, *args, **kwargs):
        return self._onDateTimeFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnDate(self, type_info, *args, **kwargs):
        return self._onDateFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnDirectory(self, type_info, *args, **kwargs):
        return self._onDirectoryFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnDuration(self, type_info, *args, **kwargs):
        return self._onDurationFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnEnum(self, type_info, *args, **kwargs):
        return self._onEnumFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnFilename(self, type_info, *args, **kwargs):
        return self._onFilenameFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnFloat(self, type_info, *args, **kwargs):
        return self._onFloatFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnGuid(self, type_info, *args, **kwargs):
        return self._onGuidFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnInt(self, type_info, *args, **kwargs):
        return self._onIntFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnString(self, type_info, *args, **kwargs):
        return self._onStringFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    def OnTime(self, type_info, *args, **kwargs):
        return self._onTimeFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Empty(*args, **kwargs):
        pass
