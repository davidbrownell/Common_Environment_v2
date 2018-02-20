# ----------------------------------------------------------------------
# |  
# |  Constants.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 12:31:51
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
import textwrap

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

TEMPORARY_FILE_EXTENSION                                = ".SourceRepositoryTools"
DYNAMIC_PLUGIN_ARCHITECTURE_FILE_EXTENSION              = ".DPA"

SETUP_ENVIRONMENT_NAME                                  = "SetupEnvironment"
SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME                = "{}_custom.py".format(SETUP_ENVIRONMENT_NAME)

ACTIVATE_ENVIRONMENT_NAME                               = "ActivateEnvironment"
ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME             = "{}_custom.py".format(ACTIVATE_ENVIRONMENT_NAME)

AGNOSTIC_OS_NAME                                        = "Agnostic"

GENERATED_DIRECTORY_NAME                                = "Generated"
GENERATED_BOOTSTRAP_JSON_FILENAME                       = "EnvironmentBootstrap.json"
GENERATED_BOOTSTRAP_DATA_FILENAME                       = "EnvironmentBootstrap.data"
GENERATED_ACTIVATION_FILENAME                           = "EnvironmentActivaton.pickle"

REPOSITORY_ID_FILENAME                                  = "__RepositoryID__"

LIBRARIES_SUBDIR                                        = "Libraries"
SCRIPTS_SUBDIR                                          = "Scripts"
TOOLS_SUBDIR                                            = "Tools"

IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME                  = "IgnoreAsBootstrapDependency"

# ----------------------------------------------------------------------
# |  Custom SetupEnvironment Methods
SETUP_ENVIRONMENT_DEPENDENCIES_METHOD_NAME              = "Dependencies"
SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME                   = "CustomActions"

SETUP_ENVIRONMENT_COMMIT_HOOK_EVENT_HANDLER             = "Commit"
SETUP_ENVIRONMENT_PUSH_HOOK_EVENT_HANDLER               = "Push"
SETUP_ENVIRONMENT_PUSHED_HOOK_EVENT_HANDLER             = "Pushed"

# ----------------------------------------------------------------------
# |  Custom ActivateEnvironment Methods
ACTIVATE_ENVIRONMENT_ACTIONS_METHOD_NAME                                    = "CustomActions"
ACTIVATE_ENVIRONMENT_CUSTOM_SCRIPT_EXTRACTOR_METHOD_NAME                    = "CustomScriptExtractors"

SCRIPT_LIST_NAME                                                            = "DevEnvScripts"

# ----------------------------------------------------------------------
REPOSITORY_ID_CONTENT_TEMPLATE                          = textwrap.dedent(
    """\
    This file is used to uniquely identify this repository for the purposes of dependency management.
    Other repositories that depend on this one will intelligently search for this file upon initial
    setup and generate information that can be used when activating development environments.
    
    **** PLEASE DO NOT MODIFY, REMOVE, OR RENAME THIS FILE, AS DOING SO WILL LIKELY BREAK OTHER REPOSITORIES! ****
    
    Friendly Name:      {name}
    GUID:               {guid}
    """)

# ----------------------------------------------------------------------
DE_FUNDAMENTAL_ROOT_NAME                                = "DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"

DE_REPO_ROOT_NAME                                       = "DEVELOPMENT_ENVIRONMENT_REPOSITORY"
DE_REPO_GENERATED_NAME                                  = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED"
DE_REPO_CONFIGURATION_NAME                              = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION"

DE_REPO_ACTIVATED_FLAG                                  = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG"
