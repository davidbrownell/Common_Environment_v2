# ----------------------------------------------------------------------
# |  
# |  v3.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-04-25 08:07:31
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def CreateMetaClass(base_class, meta_class):
    # ----------------------------------------------------------------------
    class MetaClass(base_class, metaclass=meta_class):
        pass

    # ----------------------------------------------------------------------
    
    return MetaClass
