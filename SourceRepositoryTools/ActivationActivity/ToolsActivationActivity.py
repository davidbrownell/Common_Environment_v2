# ---------------------------------------------------------------------------
# |  
# |  ToolsActivationActivity.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/24/2015 07:03:29 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
from __future__ import absolute_import 

import os
import sys

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Package

__package__ = Package.CreateName(__package__, __name__, __file__)           # <Redefining builtin> pylint: disable = W0622

from .IActivationActivity import IActivationActivity

import SourceRepositoryTools

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@staticderived
class ToolsActivationActivity(IActivationActivity):

    # ---------------------------------------------------------------------------
    Name                                    = "Tools"
    DelayExecute                            = True

    IgnoreAsToolsDirFilename                = "IgnoreAsTool"

    # ---------------------------------------------------------------------------
    @classmethod
    def _CreateCommandsImpl( cls,
                             constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        assert(constants.ToolsDir == cls.Name), (constants.ToolsDir, cls.Name)

        version_info = [] if not version_specs else version_specs.Tools

        paths = []

        for repository in repositories:
            tools_fullpath = os.path.join(repository.root, constants.ToolsDir)
            if not os.path.isdir(tools_fullpath):
                continue

            for name in os.listdir(tools_fullpath):
                fullpath = os.path.join(tools_fullpath, name)
                if not os.path.isdir(fullpath):
                    continue

                if os.path.exists(os.path.join(fullpath, cls.IgnoreAsToolsDirFilename)):
                    continue

                fullpath = SourceRepositoryTools.GetVersionedDirectory(version_info, fullpath)

                actual_paths = []

                # Add well-known suffixes to the path if the exist
                for potential_suffix in [ "bin",
                                          "sbin",
                                          os.path.join("usr", "bin"),
                                          os.path.join("usr", "sbin"),
                                        ]:
                    potential_path = os.path.join(fullpath, potential_suffix)
                    if os.path.isdir(potential_path):
                        actual_paths.append(potential_path)

                if not actual_paths:
                    actual_paths.append(fullpath)

                paths.extend(actual_paths)

        return environment.AugmentPath(paths)
