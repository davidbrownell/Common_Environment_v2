# <Invalid module name> pylint: disable = C0103
# ---------------------------------------------------------------------------
# |
# |  ActivateEnvironment_custom.py
# |
# |  David Brownell (db@DavidBrownell.com)
# |
# |  09/07/2015 08:09:46 PM
# |
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
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

from CommonEnvironment import Shell         # <Unused import> pylint: disable = W0611

# ---------------------------------------------------------------------------
def CustomActions():
    return []
