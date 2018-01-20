# ----------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-01-12 07:48:16
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Builds this Docker image"""

import os
import sys

from CommonEnvironment import Build as BuildImpl
from CommonEnvironment.Build import Docker as DockerImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

APPLICATION_NAME                            = "Docker_CommonEnvironment"

Build                                       = DockerImpl.CreateRepositoryBuildFunc( "Common_Environment",
                                                                                    os.path.join(_script_dir, "..", ".."),
                                                                                    "dbrownell",
                                                                                    "common_environment",
                                                                                    "phusion/baseimage:latest",
                                                                                    "David Brownell <db@DavidBrownell.com>",
                                                                                    repository_source_excludes=[ "/Tools/Python/v2.7.10",
                                                                                                               ],
                                                                                  )
Clean                                       = DockerImpl.CreateRepositoryCleanFunc()

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(BuildImpl.Main(BuildImpl.Configuration( name=APPLICATION_NAME,
                                                         requires_output_dir=False,
                                                       )))
    except KeyboardInterrupt:
        pass
