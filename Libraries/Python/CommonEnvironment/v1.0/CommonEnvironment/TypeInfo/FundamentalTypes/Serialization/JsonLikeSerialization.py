# ----------------------------------------------------------------------
# |  
# |  JsonLikeSerialization.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 10:18:49
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

import six

from .StringSerialization import StringSerialization

from .. import ( BoolTypeInfo,
                 FloatTypeInfo,
                 IntTypeInfo,
               )

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class JsonLikeSerialization(StringSerialization):
    """\
    Support for serialization mechanisms that support some, but not all, python types.
    """

    # ----------------------------------------------------------------------
    @classmethod
    def _SerializeItemImpl(cls, type_info, item, **custom_args):
        if isinstance(type_info, (BoolTypeInfo, FloatTypeInfo, IntTypeInfo)):
            return item

        return super(JsonLikeSerialization, cls)._SerializeItemImpl(type_info, item, **custom_args)

    # ----------------------------------------------------------------------
    @classmethod
    def _DeserializeItemImpl(cls, type_info, item, **custom_args):
        if isinstance(type_info, (BoolTypeInfo, FloatTypeInfo, IntTypeInfo)) and not isinstance(item, six.string_types):
            return item

        return super(JsonLikeSerialization, cls)._DeserializeItemImpl(type_info, item, **custom_args)
