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

import SourceRepositoryTools
from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Import all CommonEnvironment functionality necessary to implement the
# basics of environment setup and activation.

COMMON_ENVIRONMENT_PATH                     = os.path.join(SourceRepositoryTools.GetFundamentalRepository(), Constants.LIBRARIES_SUBDIR, "Python", "CommonEnvironment", "v1.0")

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
