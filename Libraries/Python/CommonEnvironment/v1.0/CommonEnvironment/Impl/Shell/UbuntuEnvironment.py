# ---------------------------------------------------------------------------
# |  
# |  UbuntuEnvironment.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/08/2015 02:24:07 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import sys

from .DebianEnvironment import DebianEnvironment

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class UbuntuEnvironment(DebianEnvironment):
    Name                                    = "Ubuntu"
    PotentialOSVersionDirectoryNames        = [ "16.04", "14.04", "12.04", "11.10", "11.04", ]
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsActive(platform_name):
        return ( "ubuntu" in platform_name or                                           # Standard Linux
                 (os.uname()[0].lower() == "linux" and "microsoft" in platform_name)    # Bash on Windows
               )
