# ----------------------------------------------------------------------
# |  
# |  ToolsActivationActivity.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-16 21:24:07
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
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

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Utilities

from SourceRepositoryTools.Impl.ActivationActivity import IActivationActivity

# ----------------------------------------------------------------------
CommonEnvironmentImports.Interface.staticderived
class ToolsActivationActivity(IActivationActivity.IActivationActivity):
    
    # ----------------------------------------------------------------------
    Name                                    = "Tools"
    DelayExecute                            = True

    IgnoreAsToolsDirFilename                = "IgnoreAsTool"

    # ----------------------------------------------------------------------
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
            tools_fullpath = os.path.join(repository.Root, constants.ToolsDir)
            if not os.path.isdir(tools_fullpath):
                continue

            for name in os.listdir(tools_fullpath):
                fullpath = os.path.join(tools_fullpath, name)
                if not os.path.isdir(fullpath):
                    continue

                if os.path.exists(os.path.join(fullpath, cls.IgnoreAsToolsDirFilename)):
                    continue

                fullpath = Utilities.GetVersionedDirectory(version_info, fullpath)

                actual_paths = []

                # Add well-known suffixes to the path if they exist
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

                paths += actual_paths

        return environment.AugmentPath(paths)
