# ---------------------------------------------------------------------------
# |  
# |  ActivateEnvironment.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/12/2015 08:01:57 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import copy
import inspect
import itertools
import os
import shutil
import sys
import textwrap

import cPickle as pickle

import __init__ as Impl

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

SourceRepositoryTools                       = Impl.SourceRepositoryTools

CallOnExit                                  = Impl.CallOnExit
CommandLine                                 = Impl.CommandLine
Package                                     = Impl.Package
QuickObject                                 = Impl.QuickObject
Shell                                       = Impl.Shell
StreamDecorator                             = Impl.StreamDecorator

__package__ = Package.CreateName(__package__, __name__, __file__)

from ..ActivationActivity.IActivationActivity import IActivationActivity, Constants
from ..ActivationActivity.PythonActivationActivity import PythonActivationActivity
from ..ActivationActivity.ScriptsActivationActivity import ScriptsActivationActivity
from ..ActivationActivity.ToolsActivationActivity import ToolsActivationActivity

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
GENERATED_ORIGINAL_ENVIRONMENT_FILENAME     = "OriginalEnvironment.data"
GENERATED_REPO_DATA_FILENAME                = "Repository.data"

CUSTOM_ACTIONS_METHOD_NAME                  = "CustomActions"

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def LoadOriginalEnvironment():
    generated_dir = os.getenv(SourceRepositoryTools.DE_REPO_GENERATED_NAME)
    assert os.path.isdir(generated_dir), generated_dir

    filename = os.path.join(generated_dir, GENERATED_ORIGINAL_ENVIRONMENT_FILENAME)
    assert os.path.isfile(filename), filename

    with open(filename) as f:
        return pickle.loads(f.read())

# ---------------------------------------------------------------------------
def LoadRepoData():
    filename = os.getenv(SourceRepositoryTools.DE_REPO_DATA_NAME)
    assert os.path.isfile(filename), filename

    with open(filename) as f:
        content = pickle.loads(f.read())

        return QuickObject( prioritized_repositories=content["prioritized_repositories"],
                            version_specs=content["version_specs"],
                          )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint( output_filename_or_stdout=CommandLine.EntryPoint.ArgumentInfo(description="Created file containing the generated content or stdout of the value is 'stdout'"),
                         repository_root=CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"),
                         configuration=CommandLine.EntryPoint.ArgumentInfo(description="Configuration value to setup; all configurations will be setup if no configurations are provided"),
                         debug=CommandLine.EntryPoint.ArgumentInfo(description="Displays additional debug information if provided"),
                         set_dependency_environment_flag=CommandLine.EntryPoint.ArgumentInfo(description="If provided, will set the dependency flag within the environment"),
                       )
@CommandLine.FunctionConstraints( output_filename_or_stdout=CommandLine.StringTypeInfo(),
                                  repository_root=CommandLine.DirectoryTypeInfo(),
                                  configuration=CommandLine.StringTypeInfo(),
                                )
def Activate( output_filename_or_stdout,
              repository_root,
              configuration,
              debug=False,
              set_dependency_environment_flag=False,
            ):
    configuration = configuration if configuration.lower() != "none" else None

    environment = Shell.GetEnvironment()

    # ---------------------------------------------------------------------------
    def Execute():
        if not os.getenv(SourceRepositoryTools.DE_REPO_DATA_NAME):
            dependency_info = Impl.TraverseDependencies(repository_root, configuration)
            
            # Check the fingerprints
            if dependency_info.fingerprint != dependency_info.calculated_fingerprint:
                status_lines = []

                status_template = "{root:<80}  :  {status}"

                for k, v in dependency_info.calculated_fingerprint.iteritems():
                    if k not in dependency_info.fingerprint:
                        status_lines.append(status_template.format(root=k, status="Added"))
                    else:
                        status_lines.append(status_template.format(root=k, status="Identical" if v == dependency_info.fingerprint[k] else "Modified"))

                for k in dependency_info.fingerprint.keys():
                    if k not in dependency_info.calculated_fingerprint:
                        status_lines.append(status_template.format(root=k, status="Removed"))

                return 1, [ Shell.Message(textwrap.dedent(
                    """\
                    ********************************************************************************
                    ********************************************************************************
                    It appears that one or more of this repository's base repositories have changed.
                    Please run '{setup}' again.

                        {status}

                    ********************************************************************************
                    ********************************************************************************
                    """).format( setup="{}{}".format(SourceRepositoryTools.SETUP_ENVIRONMENT_NAME, environment.ScriptExtension),
                                 status=StreamDecorator.LeftJustify('\n'.join(status_lines), 4),
                               )), ]

            generated_dir = os.path.join(repository_root, SourceRepositoryTools.GENERATED_DIRECTORY_NAME, configuration or "Default")
            
        else:
            dependency_info = LoadRepoData()
            generated_dir = os.getenv(SourceRepositoryTools.DE_REPO_GENERATED_NAME)
            
        if not os.path.isdir(generated_dir):
            os.makedirs(generated_dir)
        
        # Are we activating a tool repository
        is_tool_repository = Impl.RepositoryInformation.Load(repository_root).is_tool_repository
        
        if is_tool_repository:
            this_dependency_info = Impl.TraverseDependencies(repository_root, configuration)
            
            assert not this_dependency_info.version_specs.Tools
            assert not this_dependency_info.version_specs.Libraries
            
            assert len(this_dependency_info.prioritized_repositories) == 1
            tool_repository = this_dependency_info.prioritized_repositories[0]

            # Activate the repository if it hasn't been activated already
            if not any(r.id == tool_repository.id for r in dependency_info.prioritized_repositories):
                assert tool_repository.is_tool_repository == False
                tool_repository.is_tool_repository = True

                dependency_info.prioritized_repositories.append(tool_repository)
                
        # Create the methods to invoke
        methods = [ _ActivateRepoData,
                    _ActivateNames,
                    _ActivatePython,
                    _ActivateTools,
                    _ActivateScripts,
                    _ActivateCustom,
                    _ActivatePrompt,
                  ]
        
        if not is_tool_repository:
            methods = [ _ActivateOriginalEnvironment,
                        _ActivateMasterRepoData,
                      ] + methods

        args = { "constants" : Constants( SourceRepositoryTools.LIBRARIES_SUBDIR,
                                          SourceRepositoryTools.SCRIPTS_SUBDIR,
                                          SourceRepositoryTools.TOOLS_SUBDIR,
                                          SourceRepositoryTools.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME,
                                        ),
                 "environment" : environment,
                 "configuration" : configuration,
                 "repositories" : dependency_info.prioritized_repositories,
                 "version_specs" : dependency_info.version_specs,
                 "generated_dir" : generated_dir,
                 "debug" : debug,
               }

        commands = []

        for method in methods:
            commands += IActivationActivity.CallMethod(method, **args)

        return commands

    # ---------------------------------------------------------------------------
    
    rval, commands = Impl.GenerateCommands(Execute, environment, debug)

    if output_filename_or_stdout == "stdout":
        output_stream = sys.stdout
        CloseStream = lambda: None
    else:
        output_stream = open(output_filename_or_stdout, 'w')
        CloseStream = lambda: output_stream.close()

    output_stream.write(environment.GenerateCommands(commands))
    CloseStream()

    return rval

# ---------------------------------------------------------------------------
_ListConfiguration_DisplayFormats = [ "standard", "indented", ]

@CommandLine.EntryPoint( repository_root=CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"),
                         display_format=CommandLine.EntryPoint.ArgumentInfo(description="Controls how the output is displayed"),
                       )
@CommandLine.FunctionConstraints( repository_root=CommandLine.DirectoryTypeInfo(),
                                  display_format=CommandLine.EnumTypeInfo(_ListConfiguration_DisplayFormats),
                                )
def ListConfigurations( repository_root, 
                        display_format=_ListConfiguration_DisplayFormats[0],
                      ):
    display_format = display_format.lower()
    assert display_format in _ListConfiguration_DisplayFormats, display_format

    repo_info = Impl.RepositoryInformation.Load(repository_root)
    configurations = repo_info.Configurations
    
    if display_format == "standard":
        sys.stdout.write(textwrap.dedent(
            """\

            Available configurations:
            {}

            """).format('\n'.join([ "    - {}".format(config) for config in configurations ]) if configurations else "None"))
    
    elif display_format == "indented":
        sys.stdout.write('\n'.join([ "        - {}".format(config) for config in configurations ]) if configurations else "None")

    else:
        assert False, display_format

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint(repository_root=CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"))
@CommandLine.FunctionConstraints(repository_root=CommandLine.DirectoryTypeInfo())
def IsToolRepository(repository_root):
    repo_info = Impl.RepositoryInformation.Load(repository_root)
    result = repo_info.is_tool_repository

    sys.stdout.write("{}\n".format(result))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _ActivateOriginalEnvironment(generated_dir):
    d = dict(os.environ)

    elimination_funcs = [ lambda value: value == "PYTHON_BINARY",
                          lambda value: value.startswith("_ACTIVATE_ENVIRONMENT"),
                          lambda value: value.startswith("DEVELOPMENT_ENVIRONMENT"),
                        ]

    for k in list(d.keys()):
        for elimination_func in elimination_funcs:
            if elimination_func(k):
                d.pop(k)
                break

    with open(os.path.join(generated_dir, GENERATED_ORIGINAL_ENVIRONMENT_FILENAME), 'w') as f:
        f.write(pickle.dumps(d))
        
# ---------------------------------------------------------------------------
def _ActivateMasterRepoData(configuration, generated_dir):
    commands = [ Shell.Set( SourceRepositoryTools.DE_REPO_ROOT_NAME,
                            os.path.realpath(os.path.join(generated_dir, "..", "..")),
                            preserve_original=False,
                          ),
                 Shell.Set( SourceRepositoryTools.DE_REPO_GENERATED_NAME,
                            generated_dir,
                            preserve_original=False,
                          ),
               ]

    if configuration:
        commands.append(Shell.Set( SourceRepositoryTools.DE_REPO_CONFIGURATION_NAME,
                                   configuration,
                                   preserve_original=False,
                                 ))

    if not os.path.isdir(generated_dir):
        os.makedirs(generated_dir)

    return commands 

# ---------------------------------------------------------------------------
def _ActivateRepoData(environment, repositories, version_specs):
    commands = []

    filename = os.getenv(SourceRepositoryTools.DE_REPO_DATA_NAME)
    if not filename:
        filename = environment.CreateTempFilename(".RepoData{}".format(SourceRepositoryTools.TEMPORARY_FILE_EXTENSION))
        commands.append(environment.Set(SourceRepositoryTools.DE_REPO_DATA_NAME, filename, preserve_original=False))

    with open(filename, 'w') as f:
        f.write(pickle.dumps({ "prioritized_repositories" : repositories,
                               "version_specs" : version_specs,
                             }))

    return commands

# ---------------------------------------------------------------------------
def _ActivateNames(repositories):
    commands = [ Shell.Message("\n"),
               ]

    names = []
    max_name_length = 0

    for repository in repositories:
        names.append("'{}{}'".format(repository.name, " ({})".format(repository.configuration) if repository.configuration else ''))
        max_name_length = max(max_name_length, len(names[-1]))

    for repository, name in itertools.izip(repositories, names):
        commands.append(Shell.Message("Activating {name:<{max_name_length}} <{id:<20}> [{root}]...".format( name=name,
                                                                                                            max_name_length=max_name_length,
                                                                                                            id=repository.id,
                                                                                                            root=repository.root,
                                                                                                          )))
    commands.append(Shell.Message("\n"))

    return commands

# ---------------------------------------------------------------------------
def _ActivatePython(constants, environment, configuration, repositories, version_specs, generated_dir):
    commands = PythonActivationActivity.CreateCommands( constants,
                                                        environment,
                                                        configuration,
                                                        repositories,
                                                        version_specs,
                                                        generated_dir,
                                                      )

    commands.append(Shell.AugmentSet("PYTHONUNBUFFERED", "1"))

    return commands

# ---------------------------------------------------------------------------
def _ActivateScripts(constants, environment, configuration, repositories, version_specs, generated_dir):
    return ScriptsActivationActivity.CreateCommands( constants,
                                                     environment,
                                                     configuration,
                                                     repositories,
                                                     version_specs,
                                                     generated_dir,
                                                   )

# ---------------------------------------------------------------------------
def _ActivateTools(constants, environment, configuration, repositories, version_specs, generated_dir):
    return ToolsActivationActivity.CreateCommands( constants,
                                                   environment,
                                                   configuration,
                                                   repositories,
                                                   version_specs,
                                                   generated_dir,
                                                 )

# ---------------------------------------------------------------------------
def _ActivateCustom(**kwargs):
    repositories = kwargs["repositories"]

    commands = []

    for repository in repositories:
        result = IActivationActivity.CallCustomMethod( os.path.join(repository.root, SourceRepositoryTools.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                                                       CUSTOM_ACTIONS_METHOD_NAME,
                                                       **kwargs
                                                     )
        if result != None:
            commands += result

    return commands

# ---------------------------------------------------------------------------
def _ActivatePrompt(repositories, configuration):
    tool_names = []

    index = -1
    while repositories[index].is_tool_repository:
        tool_names.insert(0, repositories[index].name)
        index -= 1

    prompt = repositories[index].name
    if configuration:
        prompt += " - {}".format(configuration)

    if tool_names:
        prompt += " [{}]".format(', '.join(tool_names))
                       
    return Shell.SetCommandPrompt(prompt)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
