# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/15/2015 01:38:46 PM
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

def GetLiteral(parser, value):
    value = parser.literalNames[value]

    if value[0] == "'":
        value = value[1:]

    if value[-1] == "'":
        value = value[:-1]

    return value
