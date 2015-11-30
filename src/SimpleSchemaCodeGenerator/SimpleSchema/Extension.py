# ---------------------------------------------------------------------------
# |  
# |  Extension.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/06/2015 07:23:05 AM
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

class Extension(object):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  name,
                  allow_duplicates=False,
                ):
        self.Name                           = name
        self.AllowDuplicates                = allow_duplicates
