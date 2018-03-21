# ----------------------------------------------------------------------
# |  
# |  ActivateAndExecute.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-19 09:15:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import json
import os
import sys

import six

from SourceRepositoryTools.Impl import Utilities
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl.EnvironmentBootstrap import EnvironmentBootstrap

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def ActivateAndExecute( environment,
                        activation_repo_dir,
                        activation_configuration,                           # Can be None
                        command,
                        output_stream,
                        skip_tool_repositories=False,
                        is_dependency_environment=False,                    # Will set the corresponding flag in the activated environment
                        env_vars=None,                                      # { k : v, }
                      ):
    assert environment
    assert os.path.isdir(activation_repo_dir), activation_repo_dir
    assert command
    assert output_stream

    cl_env_vars = env_vars or {}

    bootstrap_data = EnvironmentBootstrap.Load(activation_repo_dir, environment=environment)

    if bootstrap_data.IsToolRepo and skip_tool_repositories:
        output_stream.write("Skipping '{}' because it is a tool repository.\n".format(activation_repo_dir))
        return 0

    activate_environment_script_name = environment.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME)

    activation_script = os.path.join(activation_repo_dir, activate_environment_script_name)
    assert os.path.isfile(activation_script), activation_script

    # Generate the command
    commands = [ environment.Call("{script}{config}{dependency_environment_flag}" \
                                       .format( script=activation_script,
                                                config=" {}".format(activation_configuration) if activation_configuration else '',
                                                dependency_environment_flag= " /set_dependency_environment_flag" if is_dependency_environment else '',
                                              )),
                 environment.Execute(command),
               ]

    if bootstrap_data.IsToolRepo:
        fundamental_activate_script = os.path.join(bootstrap_data.FundamentalRepo, activate_environment_script_name)
        assert os.path.isdir(fundamental_activate_script), fundamental_activate_script

        commands.insert(0, environment.Call(fundamental_activate_script))

    # Get the original environment vars
    generated_dir = Utilities.GetActivationDir( environment,
                                                bootstrap_data.FundamentalRepo,
                                                None,
                                              )
    original_environment_filename = os.path.join(generated_dir, Constants.GENERATED_ACTIVATION_ORIGINAL_ENVIRONMENT_FILENAME)
    assert os.path.isfile(original_environment_filename), original_environment_filename

    with open(original_environment_filename) as f:
        env_vars = json.load(f)

    # Augment the original environment with values provided on the command line
    for k, v in six.iteritems(cl_env_vars):
        env_vars[k] = v

    return environment.ExecuteCommands( commands,
                                        output_stream,
                                        environment=env_vars,
                                      )
