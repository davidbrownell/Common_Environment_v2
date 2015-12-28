# ---------------------------------------------------------------------------
# |  
# |  DictTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 11:38:47 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from .Impl.ObjectLikeTypeInfo import ObjectLikeTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class DictTypeInfo(ObjectLikeTypeInfo):

    ExpectedType                            = dict
    Desc                                    = "Dictionary"

    # ---------------------------------------------------------------------------
    @staticmethod
    def _HasAttribute(item, attribute_name):
        return attribute_name in item

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetAttributeValue(type_info, item, attribute_name):
        return item[attribute_name]
