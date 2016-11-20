# ---------------------------------------------------------------------------
# |  
# |  DisplayPythonLibraryModifications.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/13/2015 07:24:09 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Displays modifications made to the local Python library virtual environment.
"""

import os
import sys

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools.ActivationActivity.PythonActivationActivity import PythonActivationActivity
    from SourceRepositoryTools.ActivationActivity.Impl import ResetLibraryContent

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(output_stream=None)
def Display( output_stream=sys.stdout,
           ):
    generated_dir = os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED")
    assert os.path.isdir(generated_dir), generated_dir

    PythonActivationActivity.OutputModifications(generated_dir, output_stream)

    return 0

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
