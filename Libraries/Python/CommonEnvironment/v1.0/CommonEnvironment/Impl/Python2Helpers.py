# ----------------------------------------------------------------------
# |  
# |  Python2Helpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-03-19 14:19:36
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Helpers for Python2 code"""

import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# The 'ur' syntax can't be parsed in Python3, so only include this file
# if we are in Python2.
def ConvertUNCFilename(filename):
    return ur"\\?\{}".format(filename)