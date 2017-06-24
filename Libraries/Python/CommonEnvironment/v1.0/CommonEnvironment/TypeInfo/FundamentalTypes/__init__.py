# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 18:11:17
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

import six

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
    from .UriTypeInfo import UriTypeInfo
    
    from .. import Arity
else:
    from CommonEnvironment.TypeInfo.FundamentalTypes.BoolTypeInfo import BoolTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.DateTypeInfo import DateTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.EnumTypeInfo import EnumTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.FloatTypeInfo import FloatTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.GuidTypeInfo import GuidTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.IntTypeInfo import IntTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.StringTypeInfo import StringTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.TimeTypeInfo import TimeTypeInfo
    from CommonEnvironment.TypeInfo.FundamentalTypes.UriTypeInfo import UriTypeInfo
    
    from CommonEnvironment.TypeInfo import Arity

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

FUNDAMENTAL_TYPES                           = ( BoolTypeInfo,
                                                DateTimeTypeInfo,
                                                DateTypeInfo,
                                                DirectoryTypeInfo,
                                                DurationTypeInfo,
                                                EnumTypeInfo,
                                                FilenameTypeInfo,
                                                FloatTypeInfo,
                                                GuidTypeInfo,
                                                IntTypeInfo,
                                                StringTypeInfo,
                                                TimeTypeInfo,
                                                UriTypeInfo,
                                              )

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
    @staticmethod
    @_Interface.abstractmethod
    def OnUri(type_info, *args, **kwargs):
        raise Exception("Abstract method")
        
    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, type_info, *args, **kwargs):
        lookup = { BoolTypeInfo             : cls.OnBool,
                   DateTimeTypeInfo         : cls.OnDateTime,
                   DateTypeInfo             : cls.OnDate,
                   DirectoryTypeInfo        : cls.OnDirectory,
                   DurationTypeInfo         : cls.OnDuration,
                   EnumTypeInfo             : cls.OnEnum,
                   FilenameTypeInfo         : cls.OnFilename,
                   FloatTypeInfo            : cls.OnFloat,
                   GuidTypeInfo             : cls.OnGuid,
                   IntTypeInfo              : cls.OnInt,
                   StringTypeInfo           : cls.OnString,
                   TimeTypeInfo             : cls.OnTime,
                   UriTypeInfo              : cls.OnUri,
                 }
        
        typ = type(type_info)
        
        try:
            func = lookup[typ]
        except KeyError:
            raise Exception("'{}' was not expected".format(typ))

        return func(type_info, *args, **kwargs)
        
# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
# <Invalid argument name> pylint: disable = C0103
# <Too many return statements> pylint: disable = R0911
# <Too many braches> pylint: disable = R0912
def CreateSimpleVisitor( onBoolFunc=None,               # def Func(type_info, *args, **kwargs)
                         onDateTimeFunc=None,           # def Func(type_info, *args, **kwargs)
                         onDateFunc=None,               # def Func(type_info, *args, **kwargs)
                         onDirectoryFunc=None,          # def Func(type_info, *args, **kwargs)
                         onDurationFunc=None,           # def Func(type_info, *args, **kwargs)
                         onEnumFunc=None,               # def Func(type_info, *args, **kwargs)
                         onFilenameFunc=None,           # def Func(type_info, *args, **kwargs)
                         onFloatFunc=None,              # def Func(type_info, *args, **kwargs)
                         onGuidFunc=None,               # def Func(type_info, *args, **kwargs)
                         onIntFunc=None,                # def Func(type_info, *args, **kwargs)
                         onStringFunc=None,             # def Func(type_info, *args, **kwargs)
                         onTimeFunc=None,               # def Func(type_info, *args, **kwargs)
                         onUriFunc=None,                # def Func(type_info, *args, **kwargs)
                         onDefaultFunc=None,            # def Func(type_info, *args, **kwargs)
                       ):
    onDefaultFunc = onDefaultFunc or (lambda *args, **kwargs: None)
    
    onBoolFunc = onBoolFunc or onDefaultFunc
    onDateTimeFunc = onDateTimeFunc or onDefaultFunc
    onDateFunc = onDateFunc or onDefaultFunc
    onDirectoryFunc = onDirectoryFunc or onDefaultFunc
    onDurationFunc = onDurationFunc or onDefaultFunc
    onEnumFunc = onEnumFunc or onDefaultFunc
    onFilenameFunc = onFilenameFunc or onDefaultFunc
    onFloatFunc = onFloatFunc or onDefaultFunc
    onGuidFunc = onGuidFunc or onDefaultFunc
    onIntFunc = onIntFunc or onDefaultFunc
    onStringFunc = onStringFunc or onDefaultFunc
    onUriFunc = onUriFunc or onDefaultFunc
    onTimeFunc = onTimeFunc or onDefaultFunc

    # ----------------------------------------------------------------------
    class SimpleVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnBool(type_info, *args, **kwargs):
            return onBoolFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDateTime(type_info, *args, **kwargs):
            return onDateTimeFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDate(type_info, *args, **kwargs):
            return onDateFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDirectory(type_info, *args, **kwargs):
            return onDirectoryFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDuration(type_info, *args, **kwargs):
            return onDurationFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnEnum(type_info, *args, **kwargs):
            return onEnumFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnFilename(type_info, *args, **kwargs):
            return onFilenameFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnFloat(type_info, *args, **kwargs):
            return onFloatFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnGuid(type_info, *args, **kwargs):
            return onGuidFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnInt(type_info, *args, **kwargs):
            return onIntFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnString(type_info, *args, **kwargs):
            return onStringFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnTime(type_info, *args, **kwargs):
            return onTimeFunc(type_info, *args, **kwargs)
            
        # ----------------------------------------------------------------------
        @staticmethod
        def OnUri(type_info, *args, **kwargs):
            return onUriFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------
    
    return SimpleVisitor

# ----------------------------------------------------------------------
def CreateTypeInfo(type_, **kwargs):
    if _IsStringType(type_):
        return StringTypeInfo(**kwargs)

    for potential_type_info in [ BoolTypeInfo,
                                 DateTimeTypeInfo,
                                 DateTypeInfo,
                                 # DirectoryTypeInfo,
                                 DurationTypeInfo,
                                 # EnumTypeInfo,
                                 # FilenameTypeInfo,
                                 FloatTypeInfo,
                                 GuidTypeInfo,
                                 IntTypeInfo,
                                 # StringTypeInfo,
                                 TimeTypeInfo,
                                 UriTypeInfo,
                               ]:
        if potential_type_info.ExpectedType == type_:
            return potential_type_info(**kwargs)

    raise Exception("'{}' is not a recognized type".format(type_))
    
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if sys.version_info[0] == 2:
    # ----------------------------------------------------------------------
    def _IsStringType(t):
        return t in [ str, unicode, basestring, ]

    # ----------------------------------------------------------------------
    
else:
    # ----------------------------------------------------------------------
    def _IsStringType(t):
        return t == str

    # ----------------------------------------------------------------------
