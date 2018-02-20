# ----------------------------------------------------------------------
# |  
# |  CommonEnvironmentImports.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 12:41:56
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Note that this file will be included as part of the bootstrapping process, and
in a variety of different environments. We can't make too many assumptions about
the state of the system when we are here.
"""

import os
import sys

from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def GetFundamentalRepository():
    # Get the location of the fundamental dir. This is "../.." when invoked from a python
    # script, but more complicated when invoked as part of a frozen binary.

    value = os.getenv(Constants.DE_FUNDAMENTAL_ROOT_NAME)
    if value is None:
        # If here, we aren't running in a standard environment and are likely
        # running as part of a frozen exe. See if we are running on a system that
        # is similar to CommonEnvironment.
        assert "python" not in sys.executable.lower(), sys.executable

        potential_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if os.path.isdir(potential_dir):
            value = potential_dir

    if value is not None and value.endswith(os.path.sep):
        value = value[:-len(os.path.sep)]

    return value

# ----------------------------------------------------------------------

fundamental_repo = GetFundamentalRepository()

# We may be called with our expected version of python, or from an embedded version
# of python (which is the case when this file is called from a frozen app). Ensure that
# some of the basic libraries are included; everything in CommonEnvironment depends
# on these.
try:
    import inflect
    import six
    import wrapt

except ImportError:

    # We are using a foriegn version of python. Hard-code an import path to a known
    # location of these libraries. Because these libraries are so basic, it doesn't
    # matter which version we use; therefore pick the lowest common denominator.
    
    assert fundamental_repo

    python_root = os.path.join(fundamental_repo, "Tools", "Python", "v2.7.10")
    assert os.path.isdir(python_root), python_root

    for suffix in [ os.path.join("Windows", "Lib", "site-packages"),
                    os.path.join("Ubuntu", "lib", "python2.7", "site-packages"),
                  ]:
        potential_dir = os.path.join(python_root, suffix)
        if os.path.isdir(potential_dir):
            sys.path.insert(0, potential_dir)
            break

    # Try it again
    import inflect
    import six
    import wrapt
    
    del sys.path[0]

# ----------------------------------------------------------------------
# Import all CommonEnvironment functionality necessary to implement the
# basics of environment setup and activation.

COMMON_ENVIRONMENT_PATH                     = os.path.join(fundamental_repo, Constants.LIBRARIES_SUBDIR, "Python", "CommonEnvironment", "v1.0")

assert os.path.isdir(COMMON_ENVIRONMENT_PATH), COMMON_ENVIRONMENT_PATH

sys.path.insert(0, COMMON_ENVIRONMENT_PATH)

import CommonEnvironment

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment import Package
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import RegularExpression
from CommonEnvironment import six_plus
from CommonEnvironment import Shell
from CommonEnvironment import SourceControlManagement
from CommonEnvironment.StreamDecorator import StreamDecorator

del sys.path[0]
