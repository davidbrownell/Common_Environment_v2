# ---------------------------------------------------------------------------
# |  
# |  pyconsole.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/16/2015 10:27:37 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Launches the python console, taking care of unfortunately wonkiness on windows.
"""

import os
import subprocess
import sys

from CommonEnvironment import CommandLine

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
def EntryPoint():
    environ = os.environ

    if os.getenv("PYTHONUNBUFFERED") == "1":
        del environ["PYTHONUNBUFFERED"]

    os.system("python")

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
