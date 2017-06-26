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
"""Enhancements for the six library"""

import base64
import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Redefinig built-in type> pylint: disable = W0622
# <Unable to import> pylint: disable = E0401
# <Using variable before assignment> pylint: disable = E0601
# <No name in module> pylint: disable = E0611

if sys.version_info[0] == 2:

    # <Unused argument> pylint: disable = W0613
    # <Invalid argument name> pylint: disable = C0103
    
    # ----------------------------------------------------------------------
    def BytesToString(b, encode=False):
        if encode:
            b = base64.b64encode(b)

        return b

    # ----------------------------------------------------------------------
    def StringToBytes(s, encode=False):
        if encode:
            return base64.b64encode(s)
        
        return s

    # ----------------------------------------------------------------------
    def BytesFromString(s, decode=False):
        if decode:
            s = base64.b64decode(s)

        return s

    # ----------------------------------------------------------------------
    def StringFromBytes(b, decode=False):
        if decode:
            b = base64.b64decode(b)

        return b

else:
    # <Invalid argument name> pylint: disable = C0103

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
