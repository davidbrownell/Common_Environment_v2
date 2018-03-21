# ----------------------------------------------------------------------
# |  
# |  ActivateEnvironment.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 20:03:14
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
import textwrap

from collections import OrderedDict

import six

from SourceRepositoryTools.Impl.ActivationData import ActivationData
from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl.EnvironmentBootstrap import EnvironmentBootstrap
from SourceRepositoryTools.Impl import Utilities

from SourceRepositoryTools.Impl.ActivationActivity.IActivationActivity import IActivationActivity, \
                                                                              Constants as ConstantsObject
from SourceRepositoryTools.Impl.ActivationActivity.PythonActivationActivity import PythonActivationActivity
from SourceRepositoryTools.Impl.ActivationActivity.ToolsActivationActivity import ToolsActivationActivity
from SourceRepositoryTools.Impl.ActivationActivity.ScriptsActivationActivity import ScriptsActivationActivity

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Created file containing the generated content or stdout of the value is 'stdout'"),
                                                  repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Root of the repository"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Configuration value to setup; all configurations will be setup if no configurations are provided"),
                                                  debug=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Displays additional debug information if provided"),
                                                  set_dependency_environment_flag=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("If provided, will set the dependency flag within the environment; this flag can be used to toggle behavior for specific repositories."),
                                                  version_spec=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Overrides version specifications for tools and/or libraries. Example: '/version_spec=Tools/Python:v3.6.0'."),
                                                  no_python_libraries=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Disables the import of python libraries, which can be useful when pip installing python libraries for Library inclusion."),
                                                  no_clean=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Disables the cleaning of generated content; the default behavior is to clean as a part of every environment activiation."),
                                                  tool=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Activate a tool library at the specified folder location along with this library"),
                                                )
@CommonEnvironmentImports.CommandLine.FunctionConstraints( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                           repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                           configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                           version_spec=CommonEnvironmentImports.CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                                                           tool=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(arity='*'),
                                                         )
def Activate( output_filename_or_stdout,
              repository_root,
              configuration,
              debug=False,
              set_dependency_environment_flag=False,
              version_spec=None,
              no_python_libraries=False,
              no_clean=False,
              force=False,
              tool=None,
            ):
    """\
    Activates this repository for development activities.
    """

    configuration = configuration if configuration.lower() != "none" else None
    version_specs = version_spec or {}; del version_spec
    tools = tool or []; del tool

    environment = CommonEnvironmentImports.Shell.GetEnvironment()

    # ----------------------------------------------------------------------
    def Execute():
        commands = []

        # Load the activation data
        sys.stdout.write("\nLoading Data...\n\n")

        is_activated = bool(os.getenv(Constants.DE_REPO_ACTIVATED_FLAG))
        
        activation_data = ActivationData.Load( repository_root,
                                               configuration,
                                               environment=environment,
                                               force=force or not is_activated,
                                            )

        # Augment the version specs with those provided on the command line
        for k, v in six.iteritems(version_specs):
            keys = k.split('/')

            if keys[0] == Constants.TOOLS_SUBDIR:
                if len(keys) != 2:
                    raise Exception("'{}' is not a valid version spec; expected '{}/<Tool Name>'.".format(k, Constants.TOOLS_SUBDIR))

                name = keys[1]
                version_infos = activation_data.VersionSpecs.Tools

            elif keys[0] == Constants.LIBRARIES_SUBDIR:
                if len(keys) != 3:
                    raise Exception("'{}' is not a valid version spec; expected '{}/<Language>/<Library Name>'.".format(k, Constants.LIBRARIES_SUBDIR))

                name = keys[2]
                version_infos = activation_data.VersionSpecs.Libraries.setdefault(keys[1], [])

            else:
                raise Exception("'{}' is not a valid version spec prefix".format(keys[0]))

            found = False
            for vi in version_infos:
                if vi.Name == name:
                    vi.Version = v
                    found = True
                    break

            if not found:
                version_infos.append(configuration.VersionInfo(name, v))

        # ----------------------------------------------------------------------
        def LoadToolLibrary(tool_path):
            tool_activation_data = ActivationData.Load( tool_path,
                                                        configuration=None,
                                                        environment=environment,
                                                        force=True,
                                                      )
            if not tool_activation_data.IsToolRepo:
                raise Exception("The repository at '{}' is not a tool repository".format(tool_path))

            assert not tool_activation_data.VersionSpecs.Tools
            assert not tool_activation_data.VersionSpecs.Libraries
            assert len(tool_activation_data.PrioritizedRepos) == 1
            
            tool_repo = tool_activation_data.PrioritizedRepos[0]
            tool_repo.IsToolRepo = True

            # Add this repo as a repo to be activated if it isn't already in the list
            if not any(r.Id == tool_repo.Id for r in activation_data.PrioritizedRepos):
                activation_data.PrioritizedRepos.append(tool_repo)

        # ----------------------------------------------------------------------

        # Are we activating a tool repository?
        is_tool_repo = EnvironmentBootstrap.Load(repository_root, environment=environment).IsToolRepo
        
        if is_tool_repo:
            if force:
                raise Exception("'force' cannot be used with tool repositories")

            LoadToolLibrary(repository_root)

        for tool in tools:
            LoadToolLibrary(tool)

        # Ensure that the generated dir exists
        generated_dir = Utilities.GetActivationDir(environment, repository_root, configuration)
        
        CommonEnvironmentImports.FileSystem.MakeDirs(generated_dir)
        
        # Create the methods to invoke and the args used during invocation
        methods = [ _ActivateActivationData,
                    _ActivateNames,
                    _ActivatePython,
                    _ActivateTools,
                    _ActivateScripts,
                    _ActivateCustom,
                    _ActivatePrompt,
                  ]

        if not is_tool_repo:
            methods = [ _ActivateOriginalEnvironment,
                        _ActivateMasterRepoData,
                      ] + methods

        args = OrderedDict([ ( "constants", ConstantsObject( Constants.LIBRARIES_SUBDIR,
                                                             Constants.SCRIPTS_SUBDIR,
                                                             Constants.TOOLS_SUBDIR,
                                                             Constants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME,
                                                           ) ),
                             ( "environment", environment ),
                             ( "configuration", configuration ),
                             ( "activation_data", activation_data ),
                             ( "version_specs", activation_data.VersionSpecs ),
                             ( "generated_dir", generated_dir ),
                             ( "debug", debug ),
                             ( "no_python_libraries", no_python_libraries ),
                             ( "no_clean", no_clean ),
                             ( "repositories", activation_data.PrioritizedRepos ),
                             ( "is_tool_repo", is_tool_repo ),
                           ])

        # Invoke the methods
        for method in methods:
            method = CommonEnvironmentImports.Interface.CreateCulledCallable(method)

            result = method(args)

            if isinstance(result, list):
                commands += result
            elif result is not None:
                commands.append(result)

        return commands

    # ----------------------------------------------------------------------

    result, commands = Utilities.GenerateCommands(Execute, environment, debug)

    if output_filename_or_stdout == "stdout":
        output_stream = sys.stdout
        CloseStream = lambda: None
    else:
        output_stream = open(output_filename_or_stdout, 'w')
        CloseStream = output_stream.close

    output_stream.write(environment.GenerateCommands(commands))
    CloseStream()

    return result

# ----------------------------------------------------------------------
_ListConfigurations_DisplayFormats          = [ "standard", "indented", "json" ]

@CommonEnvironmentImports.CommandLine.EntryPoint( repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Root of the repository"),
                                                  display_format=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Controls how the output is displayed"),
                                                )
@CommonEnvironmentImports.CommandLine.FunctionConstraints( repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                           display_format=CommonEnvironmentImports.CommandLine.EnumTypeInfo(_ListConfigurations_DisplayFormats, arity='?'),
                                                         )
def ListConfigurations( repository_root,
                        display_format=_ListConfigurations_DisplayFormats[0],
                      ):
    """\
    List all configurations available for activation by this repository.
    """

    repo_info = EnvironmentBootstrap.Load(repository_root)
    
    if display_format == "json":
        items = {}

        for config_name, config_info in six.iteritems(repo_info.Configurations):
            if config_name is None:
                continue

            # This is a bare-bones representation of the data for specific scenarios. Additional
            # scenarios should add data as necessary.
            items[config_name] = { "description" : config_info.Description,
                                 }

        sys.stdout.write(json.dumps(items))
        return 0

    config_names = [ config_name for config_name in six.iterkeys(repo_info.Configurations) if config_name ]

    max_length = 30
    if config_names:
        max_length = max([ max_length, ] + [ len(config_name) for config_name in config_names ])
    

    lines = [ "{0:<{1}}{2}".format( config_name,
                                    max_length,
                                    " : {}".format(repo_info.Configurations[config_name].Description) if repo_info.Configurations[config_name].Description else '',
                                  )
              for config_name in config_names
            ]

    if display_format == "standard":
        sys.stdout.write(textwrap.dedent(
            """\

            Available configurations:
            {}

            """).format('\n'.join([ "    - {}".format(line) for line in lines ]) if lines else "None"))
    elif display_format == "indented":
        sys.stdout.write('\n'.join([ "        - {}".format(line) for line in lines ]) if lines else "None")
    else:
        assert False, display_format

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ActivateActivationData(activation_data):
    activation_data.Save()

# ----------------------------------------------------------------------
def _ActivateOriginalEnvironment(environment, generated_dir, configuration):
    original_environment = dict(os.environ)

    elimination_funcs = [ lambda value: value.startswith("PYTHON"),
                          lambda value: value.startswith("_ACTIVATE_ENVIRONMENT"),
                          lambda value: value.startswith("DEVELOPMENT_ENVIRONMENT"),
                        ]

    for k in list(six.iterkeys(original_environment)):
        for elimination_func in elimination_funcs:
            if elimination_func(k):
                del original_environment[k]
                break
    
    with open(os.path.join(generated_dir, Constants.GENERATED_ACTIVATION_ORIGINAL_ENVIRONMENT_FILENAME), 'w') as f:
        json.dump(original_environment, f)
        
# ----------------------------------------------------------------------
def _ActivateMasterRepoData(environment, generated_dir, configuration):
    commands = [ environment.Set( Constants.DE_REPO_ACTIVATED_FLAG, 
                                  "1", 
                                  preserve_original=False,
                                ),
                 environment.Set( Constants.DE_REPO_ROOT_NAME,
                                  os.path.realpath(os.path.join(generated_dir, "..", "..", "..")),
                                  preserve_original=False,
                                ),
                 environment.Set( Constants.DE_REPO_GENERATED_NAME,
                                  generated_dir,
                                  preserve_original=False,
                                ),
               ]

    if configuration:
        commands.append(environment.Set( Constants.DE_REPO_CONFIGURATION_NAME,
                                         configuration,
                                         preserve_original=False,
                                       ))
    return commands

# ----------------------------------------------------------------------
def _ActivateNames(environment, repositories):
    col_sizes = [ 45, 32, 100, ]
    
    names = []
    max_length = col_sizes[0] / 2

    for repo in repositories:
        names.append("{}{}{}".format( repo.Name,
                                      " ({})".format(repo.Configuration) if repo.Configuration else '',
                                      " [Tool]" if repo.IsToolRepo else '',
                                    ))

        max_length = max(max_length, len(names[-1]))

    template = "{{name:<{0}}}  {{guid:<{1}}}  {{data:<{2}}}".format(*col_sizes)

    return [ environment.Message(textwrap.dedent(
                """\
                Activating these repositories:

                    {header}
                    {sep}
                    {values}

                """).format( header=template.format( name="Repository Name",
                                                     guid="Id",
                                                     data="Location",
                                                   ),
                             sep=template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ], 
                                                                                      [ '-' * col_size for col_size in col_sizes ],
                                                                                    ) }),
                             values=CommonEnvironmentImports.StreamDecorator.LeftJustify( '\n'.join([ template.format( name=name,
                                                                                                                       guid=repo.Id,
                                                                                                                       data=repo.Root,
                                                                                                                     )
                                                                                                      for repo, name in six.moves.zip(repositories, names)
                                                                                                    ]),
                                                                                          4,
                                                                                        ),
                           )),
           ]

# ----------------------------------------------------------------------
def _ActivatePython(constants, environment, configuration, repositories, version_specs, generated_dir, no_python_libraries, no_clean):
    return PythonActivationActivity.CreateCommands( constants,
                                                    environment,
                                                    configuration,
                                                    repositories,
                                                    version_specs,
                                                    generated_dir,
                                                    context={ "ProcessLibraries" : not no_python_libraries,
                                                              "Clean" : not no_clean,
                                                            },
                                                  )

# ----------------------------------------------------------------------
def _ActivateTools(constants, environment, configuration, repositories, version_specs, generated_dir):
    return ToolsActivationActivity.CreateCommands( constants,
                                                   environment,
                                                   configuration,
                                                   repositories,
                                                   version_specs,
                                                   generated_dir,
                                                 )

# ----------------------------------------------------------------------
def _ActivateScripts(constants, environment, configuration, repositories, version_specs, generated_dir, no_clean):
    return ScriptsActivationActivity.CreateCommands( constants,
                                                     environment,
                                                     configuration,
                                                     repositories,
                                                     version_specs,
                                                     generated_dir,
                                                     context={ "Clean" : not no_clean,
                                                             },
                                                   )

# ----------------------------------------------------------------------
def _ActivateCustom(**kwargs):
    repositories = kwargs["repositories"]

    commands = []

    for repository in repositories:
        result = IActivationActivity.CallCustomMethod( os.path.join(repository.Root, Constants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                                                       Constants.ACTIVATE_ENVIRONMENT_ACTIONS_METHOD_NAME,
                                                       kwargs,
                                                     )
        if result is not None:
            commands += result

    return commands

# ----------------------------------------------------------------------
def _ActivatePrompt(environment, repositories, configuration, is_tool_repo):
    if is_tool_repo and os.getenv(Constants.DE_REPO_CONFIGURATION_NAME):
        assert configuration == None, configuration
        configuration = os.getenv(Constants.DE_REPO_CONFIGURATION_NAME)

    tool_names = []

    index = -1
    while repositories[index].IsToolRepo:
        tool_names.insert(0, repositories[index].Name)
        index -= 1

    prompt = repositories[index].Name
    if configuration:
        prompt += " - {}".format(configuration)

    if tool_names:
        prompt += " [{}]".format(', '.join(tool_names))

    return environment.SetCommandPrompt(prompt)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt: pass