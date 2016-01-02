# ---------------------------------------------------------------------------
# |  
# |  CustomInvocationMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/30/2015 05:01:12 PM
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

from CommonEnvironment.Compiler.InvocationMixin import InvocationMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class CustomInvocationMixin(InvocationMixin):
    pass
