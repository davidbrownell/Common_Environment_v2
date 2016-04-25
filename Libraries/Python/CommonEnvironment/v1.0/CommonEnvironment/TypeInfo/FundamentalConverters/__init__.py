# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-04-24 20:19:56
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

from ..FundamentalTypes import *

from ...Interface import Interface as InterfaceBase, \
                         abstractmethod, \
                         staticderived

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Converter(InterfaceBase):
    # ----------------------------------------------------------------------
    def __new__(cls, type_info=None, *args, **kwargs):
        # Note that we are abusing __new__ here to create an 
        # object with behavior that can be invoked like a function
        # but uses functionality provided by a derived class. Everything
        # works well until the derived class is decorated with 'staticderived',
        # which overloads __new__ to ensure that abstract methods are defined.
        # When invoked from the 'staticderived' decorator, type_info will be 
        # None.
        if type_info == None:
            return

        cls = InterfaceBase.__new__(cls)
    
        type_info_map = { BoolTypeInfo : cls.OnBool, 
                          DateTimeTypeInfo : cls.OnDateTime,
                          DateTypeInfo : cls.OnDate,
                          DurationTypeInfo : cls.OnDuration,
                          EnumTypeInfo : cls.OnEnum,
                          FilenameTypeInfo : cls.OnFilename,
                          FloatTypeInfo : cls.OnFloat,
                          GuidTypeInfo : cls.OnGuid,
                          IntTypeInfo : cls.OnInt,
                          StringTypeInfo : cls.OnString,
                          TimeTypeInfo : cls.OnTime,
                        }
    
        type_info_type = type(type_info)
        if type_info_type not in type_info_map:
            raise Exception("'{}' was unexpected".format(type_info_type))
    
        return type_info_map[type_info_type](type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnBool(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDateTime(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDate(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDuration(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnEnum(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFilename(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFloat(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnGuid(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnInt(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnString(type_info):
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnTime(type_info):
        raise Exception("Abstract method")

# ----------------------------------------------------------------------
def CreateSimpleConverter( onBool=None,
                           onDateTime=None,
                           onDate=None,
                           onDuration=None,
                           onEnum=None,
                           onFilename=None,
                           onFloat=None,
                           onGuid=None,
                           onInt=None,
                           onString=None,
                           onTime=None,
                         ):
    # ----------------------------------------------------------------------
    @staticderived
    class SimpleConverter(Converter):

        # ----------------------------------------------------------------------
        @staticmethod
        def OnBool(type_info, *args, **kwargs):
            if not onBool:
                return

            return onBool(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDateTime(type_info, *args, **kwargs):
            if not onDateTime:
                return

            return onDateTime(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDate(type_info, *args, **kwargs):
            if not onDate:
                return

            return onDate(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDuration(type_info, *args, **kwargs):
            if not onDuration:
                return

            return onDuration(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnEnum(type_info, *args, **kwargs):
            if not onEnum:
                return

            return onEnum(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnFilename(type_info, *args, **kwargs):
            if not onFilename:
                return

            return onFilename(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnFloat(type_info, *args, **kwargs):
            if not onFloat:
                return

            return onFloat(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnGuid(type_info, *args, **kwargs):
            if not onGuid:
                return

            return onGuid(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnInt(type_info, *args, **kwargs):
            if not onInt:
                return

            return onInt(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnString(type_info, *args, **kwargs):
            if not onString:
                return

            return onString(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnTime(type_info, *args, **kwargs):
            if not onTime:
                return

            return onTime(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    
    return SimpleConverter
