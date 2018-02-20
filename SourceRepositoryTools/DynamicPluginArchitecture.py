# ----------------------------------------------------------------------
# |  
# |  DynamicPluginArchitecture.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-14 17:55:43
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Contains methods that help when creating dynamic plugin architectures across
repository boundaries.

Repositories often times have to modify how scripts in other repositories operate
in a way that doesn't create a hard dependency from the base repository to the 
extension (or plugin) repository.

For example, Common_Environment defines a script called Tester, where the code is
able to compile tests written in different languages through the use of language-
specific plugins in the form of Compilers. However, these compilers are defined
in repositories outside of Common_Environment.

To address these dependencies, we create a layer of indirection through this module;
the script that is defined in the base repository will define an environment variable
that will be updated by other repositories that provide plugins for that script. When
the script is launched, it will query that environment variable and instantiate all
the plugins that have been associated with it. Care is taken to ensure that the
environment variable can be associated with a large number of plugins.
"""

import importlib
import os
import sys

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl import Utilities

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def EnumeratePlugins(environment_beacon_name):
    filename = os.getenv(environment_beacon_name)
    if not filename or not os.path.isfile(filename):
        return

    lines = open(filename).readlines()
    for module_name in [ line.strip() for line in lines if line.strip() ]:
        yield LoadModule(module_name)

# ----------------------------------------------------------------------
def LoadModule(filename):
    assert os.path.isfile(filename), filename

    filename = os.path.realpath(filename)

    path, name = os.path.split(filename)
    name = os.path.splitext(name)[0]

    sys.path.insert(0, path)
    with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
        return importlib.import_module(name)

# ----------------------------------------------------------------------
def CreateRegistrationStatements( environment_beacon_name,
                                  directory,
                                  is_valid_func,        # def Func(fullpath, name, ext) -> Bool
                                ):
    assert os.path.isdir(directory), directory

    filenames = []

    for item in os.listdir(directory):
        fullpath = os.path.join(directory, item)
        if not os.path.isfile(fullpath):
            continue

        name, ext = os.path.splitext(item)

        if is_valid_func(fullpath, name, ext):
            filenames.append(fullpath)

    if not filenames:
        return []

    # We are writing names to a file rather than the environment, as the environment
    # can only store values of a limited size and these lists can get pretty large.
    return Utilities.DelayExecute(_DelayInit, environment_beacon_name, filenames)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _DelayInit(environment_beacon_name, filenames):
    commands = []
    new_filenames = []

    source_filename = os.getenv(environment_beacon_name)
    if not source_filename:
        source_filename = CommonEnvironmentImports.Shell.GetEnvironment().CreateTempFilename("{}{}".format( Constants.DYNAMIC_PLUGIN_ARCHITECTURE_FILE_EXTENSION,
                                                                                                            Constants.TEMPORARY_FILE_EXTENSION,
                                                                                                          ))
        commands.append(CommonEnvironmentImports.Shell.Set(environment_beacon_name, source_filename, preserve_original=False))
        os.environ[environment_beacon_name] = source_filename

    elif os.path.isfile(source_filename):
        for line in [ line.strip() for line in open(source_filename).readlines() if line.strip() ]:
            if os.path.isfile(line):
                new_filenames.append(line)

    for filename in filenames:
        if filename not in new_filenames:
            new_filenames.append(filename)

    with open(source_filename, 'w') as f:
        f.write("{}\n".format('\n'.join(sorted(new_filenames))))

    return commands
