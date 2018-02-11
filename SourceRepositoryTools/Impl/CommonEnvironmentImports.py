# ----------------------------------------------------------------------
# |  
# |  CommonEnvironmentImports.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-03-20 07:34:40
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
This functionality is used very early in the activation process,
and we cannot rely on standard python activation processes. Import
some basic functionality manually.
"""

import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
import Constants
del sys.path[0]

# ----------------------------------------------------------------------
# This code will be called extremely early in the activation cycle, and sometimes
# outside of the Tools dir (as is the case when executed as a Mercurial plugin,
# which uses an embedded version of Python). There are some modules (like six) that
# are absoluately critical to everything in CommonEnvironment and need to be loaded
# in all scenarios. As a fail safe, hard code a path for some of these libraries if
# they aren't otherwise available.
try:
    import six
except ImportError:
    # At this point, use a python dir that represents the lowest common denominator.
    # These libraries are so fundamental that they won't be doing anything OS-
    # specific, so any path will do.
    python_root = os.path.realpath(os.path.join(Constants.DE_FUNDAMENTAL, "Tools", "Python", "v2.7.10"))
    assert os.path.isdir(python_root), python_root

    for potential_suffix in [ os.path.join("Windows", "Lib", "site-packages"),
                              os.path.join("Ubuntu", "lib", "python2.7", "site-packages"),
                            ]:
        potential_path = os.path.join(python_root, potential_suffix)
        if os.path.isdir(potential_path):
            sys.path.insert(0, potential_path)
            break

    # Try it agian
    import inflect
    import six
    import wrapt
    
    del sys.path[0]

# ----------------------------------------------------------------------
# |  COMMON_ENVIRONMENT_PATH
COMMON_ENVIRONMENT_PATH                     = os.path.join(Constants.DE_FUNDAMENTAL, "Libraries", "Python", "CommonEnvironment", "v1.0")
assert os.path.isdir(COMMON_ENVIRONMENT_PATH), COMMON_ENVIRONMENT_PATH

sys.path.insert(0, COMMON_ENVIRONMENT_PATH)

import CommonEnvironment

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Package
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import RegularExpression
from CommonEnvironment import six_plus
from CommonEnvironment import Shell
from CommonEnvironment import SourceControlManagement
from CommonEnvironment.StreamDecorator import StreamDecorator

ModifiableValue = CommonEnvironment.ModifiableValue

del sys.path[0]
