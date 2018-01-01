# ----------------------------------------------------------------------
# |  
# |  DictTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 07:51:56
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from CommonEnvironment.Interface import staticderived

from . import TypeInfo
from .Impl.ObjectLikeTypeInfo import ObjectLikeTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class DictTypeInfo(ObjectLikeTypeInfo):

    ExpectedType                            = dict
    Desc                                    = "Dictionary"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetAttributeValue(type_info, item, attribute_name):
        return item[attribute_name]
