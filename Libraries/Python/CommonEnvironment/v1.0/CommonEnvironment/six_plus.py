# ----------------------------------------------------------------------
# |  
# |  six_plus.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-03-21 07:48:53
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\Enhancements for the six library"""

import base64
import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

if sys.version_info[0] == 2:
    # ----------------------------------------------------------------------
    def BytesToString(b, encode=False):
        return b

    # ----------------------------------------------------------------------
    def StringToBytes(s, encode=False):
        return s

    # ----------------------------------------------------------------------
    def BytesFromString(s, decode=False):
        return s

    # ----------------------------------------------------------------------
    def StringFromBytes(b, decode=False):
        return b

else:
    # ----------------------------------------------------------------------
    def BytesToString(b, encode=False):
        if encode:
            b = base64.b64encode(b)

        return str(b, "utf-8")

    # ----------------------------------------------------------------------
    def StringToBytes(s, encode=False):
        if encode:
            return base64.b64encode(s)

        return bytearray(s, "utf-8")

    # ----------------------------------------------------------------------
    def BytesFromString(s, decode=False):
        if decode:
            return base64.b64decode(s)

        return StringToBytes(s)

    # ----------------------------------------------------------------------
    def StringFromBytes(b, decode=False):
        if decode:
            return BytesToString(base64.b64decode(b))

        return BytesToString(b)
