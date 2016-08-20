# ---------------------------------------------------------------------------
# |  
# |  FundamentalTypes.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 09:59:33 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <Unused import> pylint: disable = W0611

from CommonEnvironment import Interface as _Interface

from . import Arity
from .Impl.FundamentalTypeInfo import FundamentalTypeInfo

from .BoolTypeInfo import BoolTypeInfo
from .DateTimeTypeInfo import DateTimeTypeInfo
from .DateTypeInfo import DateTypeInfo
from .DurationTypeInfo import DurationTypeInfo
from .EnumTypeInfo import EnumTypeInfo
from .FilenameTypeInfo import FilenameTypeInfo, DirectoryTypeInfo
from .FloatTypeInfo import FloatTypeInfo
from .GuidTypeInfo import GuidTypeInfo
from .IntTypeInfo import IntTypeInfo
from .StringTypeInfo import StringTypeInfo
from .TimeTypeInfo import TimeTypeInfo

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Visitor(_Interface.Interface):

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnBool(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDateTime(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDate(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDuration(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnEnum(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnFilename(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnDirectory(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnFloat(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnGuid(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnInt(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnString(type_info):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def OnTime(type_info):
        raise Exception("Abstract method")

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Accept(type_info, visitor):
    if isinstance(type_info, BoolTypeInfo):
        visitor.OnBool(type_info)
    elif isinstance(type_info, DateTimeTypeInfo):
        visitor.OnDateTime(type_info)
    elif isinstance(type_info, DateTypeInfo):
        visitor.OnDate(type_info)
    elif isinstance(type_info, DurationTypeInfo):
        visitor.OnDuration(type_info)
    elif isinstance(type_info, EnumTypeInfo):
        visitor.OnEnum(type_info)
    elif isinstance(type_info, FilenameTypeInfo):
        visitor.OnFilename(type_info)
    elif isinstance(type_info, DirectoryTypeInfo):
        visitor.OnDirectory(type_info)
    elif isinstance(type_info, FloatTypeInfo):
        visitor.OnFloat(type_info)
    elif isinstance(type_info, GuidTypeInfo):
        visitor.OnGuid(type_info)
    elif isinstance(type_info, IntTypeInfo):
        visitor.OnInt(type_info)
    elif isinstance(type_info, StringTypeInfo):
        visitor.OnString(type_info)
    elif isinstance(type_info, TimeTypeInfo):
        visitor.OnTime(type_info)
    else:
        raise Exception("'{}' was not expected".format(type(type_info)))
