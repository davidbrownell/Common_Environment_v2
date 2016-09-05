# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 08:05:37
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

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Serialization(_Interface.Interface):

    # ----------------------------------------------------------------------
    @classmethod
    def SerializeItems(cls, type_info, items):
        type_info.ValidateArity(items)

        if type_info.Arity.IsOptional and items == None:
            return None

        elif type_info.Arity.IsCollection:
            return [ cls.SerializeItem(type_info, item) for item in items ]

        return cls.SerializeItem(type_info, items)

    # ----------------------------------------------------------------------
    @classmethod
    def DeserializeItems(cls, type_info, items):
        type_info.ValidateArity(items)

        if type_info.Arity.IsOptional and items == None:
            return None

        elif type_info.Arity.IsCollection:
            return [ cls.DeserializeItems(type_info, item) for item in items ]

        return cls.DeserializeItems(type_info, items)

    # ----------------------------------------------------------------------
    @classmethod
    def SerializeItem(cls, type_info, item, **custom_args):
        type_info.ValidateItem(item)
        return cls._SerializeItemImpl(type_info, item, **custom_args)

    # ----------------------------------------------------------------------
    @staticmethod
    def DeserialieItem(cls, type_info, item, **custom_args):
        item = cls._DeserializeItemImpl(type_info, item, **custom_args)

        type_info.ValidateItem(item)
        return item

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def _SerializeItemImpl(type_info, item):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @_Interface.abstractmethod
    def _DeserializeItemImpl(type_info, item):
        raise Exception("Abstract method")
