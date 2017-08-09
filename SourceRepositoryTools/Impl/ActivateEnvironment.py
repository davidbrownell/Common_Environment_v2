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
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import copy
import itertools
import json
import os
import sys
import textwrap

import six

import six.moves.cPickle as pickle

import CommonEnvironmentImports

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

with CommonEnvironmentImports.Package.NameInfo(__package__) as ni:
    __package__ = ni.created

    from .. import Constants

    from ..ActivationActivity.IActivationActivity import IActivationActivity, Constants as ConstantsObject
    from ..ActivationActivity.PythonActivationActivity import PythonActivationActivity
    from ..ActivationActivity.ScriptsActivationActivity import ScriptsActivationActivity
    from ..ActivationActivity.ToolsActivationActivity import ToolsActivationActivity

    __package__ = ni.original

Impl                                        = CommonEnvironmentImports.Package.ImportInit()

# ----------------------------------------------------------------------
Shell                                       = CommonEnvironmentImports.Shell
StreamDecorator                             = CommonEnvironmentImports.StreamDecorator

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
GENERATED_ORIGINAL_ENVIRONMENT_FILENAME     = "OriginalEnvironment.json"
CUSTOM_ACTIONS_METHOD_NAME                  = "CustomActions"

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def LoadOriginalEnvironment():
    generated_dir = os.getenv(Constants.DE_REPO_GENERATED_NAME)
    assert os.path.isdir(generated_dir), generated_dir

    filename = os.path.join(generated_dir, GENERATED_ORIGINAL_ENVIRONMENT_FILENAME)
    assert os.path.isfile(filename), filename

    with open(filename, 'r') as f:
        return json.load(f)

# ---------------------------------------------------------------------------
def LoadRepoData():
    filename = os.getenv(Constants.DE_REPO_DATA_NAME)
    assert os.path.isfile(filename), filename

    with open(filename, 'rb') as f:
        content = pickle.load(f)

        return CommonEnvironmentImports.QuickObject( prioritized_repositories=content["prioritized_repositories"],
                                                     version_specs=content["version_specs"],
                                                   )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Created file containing the generated content or stdout of the value is 'stdout'"),
                                                  repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Configuration value to setup; all configurations will be setup if no configurations are provided"),
                                                  debug=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Displays additional debug information if provided"),
                                                  set_dependency_environment_flag=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="If provided, will set the dependency flag within the environment"),
                                                  version_spec=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Overrides version specifications for tools and/or libraries. Example: '/version_spec=Tools/Python:v3.6.0'."),
                                                  no_python_libraries=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Disables the import of python libraries, which can be useful when pip installing python libraries for Library inclusion."),
                                                  no_clean=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Disables the cleaning of generated content; the default behavior is to clean as a part of every environment activiation."),
                                                )
@CommonEnvironmentImports.CommandLine.FunctionConstraints( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                           repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                           configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                           version_spec=CommonEnvironmentImports.CommandLine.DictTypeInfo( arity='?',
                                                                                                                           require_exact_match=False,
                                                                                                                         ),
                                                         )
def Activate( output_filename_or_stdout,
              repository_root,
              configuration,
              debug=False,
              set_dependency_environment_flag=False,
              version_spec=None,
              no_python_libraries=False,
              no_clean=False,
            ):
    configuration = configuration if configuration.lower() != "none" else None
    cl_version_specs = version_spec or {}

    environment = Shell.GetEnvironment()

    # ---------------------------------------------------------------------------
    def Execute():
        if not os.getenv(Constants.DE_REPO_DATA_NAME):
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
                    """).format( setup="{}{}".format(Constants.SETUP_ENVIRONMENT_NAME, environment.ScriptExtension),
                                 status=StreamDecorator.LeftJustify('\n'.join(status_lines), 4),
                               )), ]

            generated_dir = os.path.join(repository_root, Constants.GENERATED_DIRECTORY_NAME, environment.CategoryName, configuration or "Default")
            
        else:
            dependency_info = LoadRepoData()
            generated_dir = os.getenv(Constants.DE_REPO_GENERATED_NAME)
            
        if not os.path.isdir(generated_dir):
            os.makedirs(generated_dir)
        
        # Augment the version specs with those provided on the command line.
        for k, v in six.iteritems(cl_version_specs):
            keys = k.split('/')

            if keys[0] == Constants.TOOLS_SUBDIR:
                if len(keys) != 2:
                    raise Exception("'{}' is not a valid tool version spec; expected '{}/<Tool Name>'.".format(k, Constants.TOOLS_SUBIDR))

                name = keys[1]
                version_infos = dependency_info.version_specs.Tools

            elif keys[0] == Constants.LIBRARIES_SUBDIR:
                if len(keys) != 3:
                    raise Exception("'{}' is not a valid libraries version spec; expected '{}/<Language>/<Libary Name>'.".format(k, Constants.LIBRARIES_SUBDIR))

                name = keys[2]
                version_infos = dependency_info.version_specs.Libraries.setdefault(keys[1], [])

            else:
                raise Exception("'{}' is not a valid version spec prefix".format(keys[0]))

            found = False
            for vi in version_infos:
                if vi.Name == name:
                    vi.Version = v
                    found = True
                    break

            if not found:
                version_infos.append(CommonEnvironmentImports.QuickObject( Name=name, 
                                                                           Version=v,
                                                                         ))

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
            
            if len(dependency_info.prioritized_repositories) == 1:
                return 1, [ Shell.Message(textwrap.dedent(
                    """\
                    ********************************************************************************
                    ********************************************************************************
                    A tool repository may not be activated in isolation. Please activate a standard
                    repository and then activate this one.

                    ********************************************************************************
                    ********************************************************************************
                    """)), ]
                
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

        args = { "constants" : ConstantsObject( Constants.LIBRARIES_SUBDIR,
                                                Constants.SCRIPTS_SUBDIR,
                                                Constants.TOOLS_SUBDIR,
                                                Constants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME,
                                              ),
                 "environment" : environment,
                 "configuration" : configuration,
                 "repositories" : dependency_info.prioritized_repositories,
                 "version_specs" : dependency_info.version_specs,
                 "generated_dir" : generated_dir,
                 "debug" : debug,
                 "is_tool_repository" : is_tool_repository,
                 "no_python_libraries" : no_python_libraries,
                 "no_clean" : no_clean,
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

@CommonEnvironmentImports.CommandLine.EntryPoint( repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"),
                                                  display_format=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Controls how the output is displayed"),
                                                )
@CommonEnvironmentImports.CommandLine.FunctionConstraints( repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                           display_format=CommonEnvironmentImports.CommandLine.EnumTypeInfo(_ListConfiguration_DisplayFormats),
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
@CommonEnvironmentImports.CommandLine.EntryPoint(repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"))
@CommonEnvironmentImports.CommandLine.FunctionConstraints(repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo())
def IsToolRepository( repository_root,
                      json=False,
                    ):
    repo_info = Impl.RepositoryInformation.Load(repository_root)
    
    if json:
        import json as json_mod

        json_mod.dump( repo_info.ToJsonObj(),
                       sys.stdout,
                     )
    else:
        sys.stdout.write(str(repo_info.is_tool_repository))

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
        json.dump(d, f)
        
# ---------------------------------------------------------------------------
def _ActivateMasterRepoData(configuration, generated_dir):
    commands = [ Shell.Set( Constants.DE_REPO_ROOT_NAME,
                            os.path.realpath(os.path.join(generated_dir, "..", "..", "..")),
                            preserve_original=False,
                          ),
                 Shell.Set( Constants.DE_REPO_GENERATED_NAME,
                            generated_dir,
                            preserve_original=False,
                          ),
               ]

    if configuration:
        commands.append(Shell.Set( Constants.DE_REPO_CONFIGURATION_NAME,
                                   configuration,
                                   preserve_original=False,
                                 ))

    if not os.path.isdir(generated_dir):
        os.makedirs(generated_dir)

    return commands 

# ---------------------------------------------------------------------------
def _ActivateRepoData(environment, repositories, version_specs):
    commands = []

    filename = os.getenv(Constants.DE_REPO_DATA_NAME)
    if not filename:
        filename = environment.CreateTempFilename(".RepoData{}".format(Constants.TEMPORARY_FILE_EXTENSION))
        commands.append(environment.Set(Constants.DE_REPO_DATA_NAME, filename, preserve_original=False))

    with open(filename, 'wb') as f:
        pickle.dump( { "prioritized_repositories" : repositories,
                       "version_specs" : version_specs,
                     },
                     f,
                   )

    return commands

# ---------------------------------------------------------------------------
def _ActivateNames(repositories):
    col_sizes = [ 40, 32, 100, ]
    names = []
    max_length = 0

    for repo in repositories:
        names.append("{}{}".format( repo.name,
                                    '' if not repo.configuration else " ({})".format(repo.configuration),
                                  ))
        max_length = max(max_length, len(names[-1]))

    col_sizes[0] = max(col_sizes[0], max_length)
    
    display_template = "{{name:<{0}}}  {{guid:<{1}}}  {{data:<{2}}}".format(*col_sizes)

    return [ Shell.Message(textwrap.dedent(
        """\
        
        Activating these repositories:

            {header}
            {sep}
            {values}

        """).format( header=display_template.format( name="Repository Name",
                                                     guid="Id",
                                                     data="Location",
                                                   ),
                     sep=display_template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ],
                                                                                      [ '-' * col_size for col_size in col_sizes ],
                                                                                    ) }),
                     values=StreamDecorator.LeftJustify( '\n'.join([ display_template.format( name=name,
                                                                                              guid=repo.id,
                                                                                              data=repo.root,
                                                                                            )
                                                                     for repo, name in six.moves.zip(repositories, names)
                                                                   ]),
                                                          4,
                                                       ),
                   )), ]

# ---------------------------------------------------------------------------
def _ActivatePython(constants, environment, configuration, repositories, version_specs, generated_dir, no_python_libraries, no_clean):
    commands = PythonActivationActivity.CreateCommands( constants,
                                                        environment,
                                                        configuration,
                                                        repositories,
                                                        version_specs,
                                                        generated_dir,
                                                        # Context is required because we are delay executing the commands
                                                        context={ "ProcessLibraries" : not no_python_libraries, 
                                                                  "Clean" : not no_clean,
                                                                },
                                                      )

    return commands

# ---------------------------------------------------------------------------
def _ActivateScripts(constants, environment, configuration, repositories, version_specs, generated_dir, no_clean):
    return ScriptsActivationActivity.CreateCommands( constants,
                                                     environment,
                                                     configuration,
                                                     repositories,
                                                     version_specs,
                                                     generated_dir,
                                                     # Context is required because we are delay-executing the commands
                                                     context={ "Clean" : not no_clean,
                                                             },
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
        result = IActivationActivity.CallCustomMethod( os.path.join(repository.root, Constants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                                                       CUSTOM_ACTIONS_METHOD_NAME,
                                                       **kwargs
                                                     )
        if result != None:
            commands += result

    return commands

# ---------------------------------------------------------------------------
def _ActivatePrompt(repositories, configuration, is_tool_repository):
    if is_tool_repository and os.getenv(Constants.DE_REPO_CONFIGURATION_NAME):
        assert configuration == None, configuration
        configuration = os.getenv(Constants.DE_REPO_CONFIGURATION_NAME)
    
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
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main( command_line_keyword_separator='_EQ_' if Shell.GetEnvironment().Name == "Windows" else '=',
                                                           ))
    except KeyboardInterrupt: pass
