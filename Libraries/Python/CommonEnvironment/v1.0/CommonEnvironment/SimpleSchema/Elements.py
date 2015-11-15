# ---------------------------------------------------------------------------
# |  
# |  Elements.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/07/2015 10:44:20 AM
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

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class Arity(object):

    # ---------------------------------------------------------------------------
    def __init__(self, min, max=None):
        self.Min                            = min
        self.Max                            = max

    # ---------------------------------------------------------------------------
    def IsOptional(self):
        return self.Min == 0 and self.Max == 1

    # ---------------------------------------------------------------------------
    def IsCollection(self):
        return self.Max == None or self.Max > 1
