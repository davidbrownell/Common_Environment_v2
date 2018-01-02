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
