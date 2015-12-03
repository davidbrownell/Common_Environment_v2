# ---------------------------------------------------------------------------
# |  
# |  ShowWindow.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/26/2015 05:30:28 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Shows or hides a window."""

import os
import sys

import win32gui
import win32con

from CommonEnvironment import CommandLine

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(title=CommandLine.StringTypeInfo())
def Show(title):
    return _Impl(title, win32con.SW_SHOW)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(title=CommandLine.StringTypeInfo())
def Hide(title):
    return _Impl(title, win32con.SW_HIDE)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _Impl(title, show_value):
    for prefix in [ '', 
                    "Administrator: ", 
                    "Administrator:  ",
                  ]:
        handle = win32gui.FindWindow(None, "{}{}".format(prefix, title))
        if handle:
            break

    if not handle:
        return -1

    win32gui.ShowWindow(handle, show_value)
    return 0

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
