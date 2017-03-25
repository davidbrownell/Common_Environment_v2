# ----------------------------------------------------------------------
# |  
# |  Constants.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-03-20 07:31:48
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
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

TEMPORARY_FILE_EXTENSION                    = ".SourceRepositoryTools"

SETUP_ENVIRONMENT_NAME                      = "SetupEnvironment"
ACTIVATE_ENVIRONMENT_NAME                   = "ActivateEnvironment"

SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME    = "{}_custom.py".format(SETUP_ENVIRONMENT_NAME)
ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME = "{}_custom.py".format(ACTIVATE_ENVIRONMENT_NAME)

AGNOSTIC_OS_NAME                            = "Agnostic"
LINUX_OS_NAME                               = "Linux"

INSTALL_LOCATION_FILENAME                   = "InstallLocation.txt"
INSTALL_BINARY_FILENAME                     = "binaries.tar.gz"

GENERATED_DIRECTORY_NAME                    = "Generated"
GENERATED_BOOTSTRAP_FILENAME                = "EnvironmentBootstrap.data"

REPOSITORY_ID_FILENAME                      = "__RepositoryID__"

LIBRARIES_SUBDIR                            = "Libraries"
SCRIPTS_SUBDIR                              = "Scripts"
TOOLS_SUBDIR                                = "Tools"

IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME = "IgnoreAsBootstrapDependency"

# ----------------------------------------------------------------------
DE_FUNDAMENTAL_ROOT_NAME                    = "DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"                     # Root of the fundamental repository
DE_REPO_ROOT_NAME                           = "DEVELOPMENT_ENVIRONMENT_REPOSITORY"
DE_REPO_CONFIGURATION_NAME                  = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION"
DE_REPO_GENERATED_NAME                      = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED"
DE_REPO_DATA_NAME                           = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_DATA"

# DE_FUNDAMENTAL
assert os.getenv(DE_FUNDAMENTAL_ROOT_NAME)

DE_FUNDAMENTAL = os.getenv(DE_FUNDAMENTAL_ROOT_NAME)
if DE_FUNDAMENTAL.endswith(os.path.sep):
    DE_FUNDAMENTAL = DE_FUNDAMENTAL[:-len(os.path.sep)]

assert os.path.isdir(DE_FUNDAMENTAL), DE_FUNDAMENTAL

# PYTHON_BINARY
assert os.getenv("PYTHON_BINARY")
PYTHON_BINARY = os.getenv("PYTHON_BINARY")
os.path.isfile(PYTHON_BINARY), PYTHON_BINARY
