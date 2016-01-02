# ---------------------------------------------------------------------------
# |  
# |  Decorator.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/28/2015 07:48:09 AM
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

import wrapt

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
def GetDecorator(function):
    if not hasattr(function, "_self_wrapper"):
        return

    return getattr(function._self_wrapper, "_im_self", function._self_wrapper)

# ---------------------------------------------------------------------------
def EnumDecorators(function):
    while function:
        decorator = GetDecorator(function)
        if decorator:
            yield decorator

        function = getattr(function, "__wrapped__", None)
