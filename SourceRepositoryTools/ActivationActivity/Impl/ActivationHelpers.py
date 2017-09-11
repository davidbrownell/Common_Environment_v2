# ----------------------------------------------------------------------
# |  
# |  ActivationHelpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-09-11 07:35:58
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Functionality that helps when activating environments.
"""

import os
import sys

from CommonEnvironment import Package

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from .. import Impl as ActivationActivity
    
    __package__ = ni.original

# ----------------------------------------------------------------------
WriteLibraryInfo                            = ActivationActivity.WriteLibraryInfo
ActivateLibraries                           = ActivationActivity.ActivateLibraries
ActivateLibraryScripts                      = ActivationActivity.ActivateLibraryScripts
CreateCleanSymLinkStatements                = ActivationActivity.CreateCleanSymLinkStatements
