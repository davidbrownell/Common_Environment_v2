﻿# ---------------------------------------------------------------------------
# |  
# |  SetupEnvironment.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/08/2015 03:12:52 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Sets up an environment for development.
"""

import inspect
import os
import sys
import textwrap

from collections import OrderedDict

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

import __init__ as Impl

SourceRepositoryTools                       = Impl.SourceRepositoryTools

CommandLine                                 = Impl.CommandLine
QuickObject                                 = Impl.QuickObject
Shell                                       = Impl.Shell
StreamDecorator                             = Impl.StreamDecorator

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
CUSTOM_DEPENDENCIES_METHOD_NAME             = "Dependencies"
CUSTOM_ACTIONS_METHOD_NAME                  = "CustomActions"

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint( output_filename_or_stdout=CommandLine.EntryPoint.ArgumentInfo(description="Created file containing the generated content or stdout if the value is 'stdout'"),
                         repository_root=CommandLine.EntryPoint.ArgumentInfo(description="Root of the repository"),
                         debug=CommandLine.EntryPoint.ArgumentInfo(description="Displays additional debug information if provided"),
                         configuration=CommandLine.EntryPoint.ArgumentInfo(description="Configuration value to setup; all configurations will be setup if no configurations are provided."),
                       )
@CommandLine.FunctionConstraints( output_filename_or_stdout=CommandLine.StringTypeInfo(),
                                  repository_root=CommandLine.DirectoryTypeInfo(),
                                  configuration=CommandLine.StringTypeInfo(arity='*'),
                                )
def EntryPoint( output_filename_or_stdout,
                repository_root,
                debug=False,
                configuration=None,
              ):
    configuration = configuration or []
    environment = Shell.GetEnvironment()
    
    # Tools must be initially installed, as other methods will depend on their successful
    # installation.

    # ---------------------------------------------------------------------------
    def Execute():
        commands = []
        
        tools_subdir = os.path.join(repository_root, SourceRepositoryTools.TOOLS_SUBDIR)
        if os.path.isdir(tools_subdir):
            for name, path in [ (name, os.path.join(tools_subdir, name)) for name in os.listdir(tools_subdir) if os.path.isdir(os.path.join(tools_subdir, name)) ]:
                version_paths = [ os.path.join(path, item) for item in os.listdir(path) if os.path.isdir(os.path.join(path, item)) ]
                if not version_paths:
                    version_paths = [ path, ]

                # ---------------------------------------------------------------------------
                def OnCustomizedPathError(path, error_string):
                    commands.append(Shell.Message("WARNING: {}".format(s)))
                    return path

                # ---------------------------------------------------------------------------
                
                for version_path in version_paths:
                    version_path = SourceRepositoryTools.GetCustomizedPathImpl(version_path, OnCustomizedPathError, environment=environment)

                    # On some machines, binaries are expected to be in a well-defined location specified at
                    # compile time (actually, configuration time). Therefore, the binaries that we have created
                    # to eliminate the potential for change need to be installed to the location that they
                    # were originally configured for.
                    
                    potential_install_location = os.path.join(version_path, SourceRepositoryTools.INSTALL_LOCATION_FILENAME)
                    potential_install_binary = os.path.join(version_path, SourceRepositoryTools.INSTALL_BINARY_FILENAME)
                    
                    if os.path.isfile(potential_install_location) and os.path.isfile(potential_install_binary):
                        commands.append(environment.CreateInstallBinaryCommand(potential_install_location, potential_install_binary))

        return commands + \
               SourceRepositoryTools.DelayExecuteWithPython( SourceRepositoryTools.PYTHON_BINARY,
                                                             _EntryPointPostInstall,
                                                             repository_root,
                                                             debug,
                                                             configuration,
                                                           )

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
# |
# |  Private Types
# |
# ---------------------------------------------------------------------------

# Note that the following types MUST be defined at the global level of this file 
# to properly support pickling. Removing or modifying these classes will break
# existing code.

# ---------------------------------------------------------------------------
class _EnhancedConfiguration(object):
    def __init__( self,
                  dependencies,
                  version_specs,
                  fingerprint,
                ):
        self.Dependencies                   = dependencies
        self.VersionSpecs                   = version_specs
        self.Fingerprint                    = fingerprint

# ---------------------------------------------------------------------------
class _EnhancedDependency(SourceRepositoryTools.Dependency):
    def __init__( self,
                  dependency,
                  repository_root,
                ):
        super(_EnhancedDependency, self).__init__( dependency.Id,
                                                   dependency.FriendlyName,
                                                   dependency.Configuration,
                                                 )
        self.RepositoryRoot                 = repository_root

# ---------------------------------------------------------------------------
# |
# |  Private Functions
# |
# ---------------------------------------------------------------------------
def _EntryPointPostInstall(repository_root, debug, optional_configuration_names):
    environment = Shell.GetEnvironment()

    # ---------------------------------------------------------------------------
    def Execute():
        setup_methods = [ _SetupBootstrap,
                          _SetupCustom,
                          _SetupShortcuts,
                          _SetupGenerated,
                        ]

        potential_customization_filename = os.path.join(repository_root, SourceRepositoryTools.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)
        if os.path.isfile(potential_customization_filename):
            customization_name = os.path.splitext(SourceRepositoryTools.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)[0]

            sys.path.insert(0, repository_root)
            customization_mod = __import__(customization_name)
            del sys.path[0]

        else:
            customization_mod = None

        commands = []

        for func in setup_methods:
            these_commands = func( environment,
                                   repository_root,
                                   customization_mod,
                                   debug,
                                   optional_configuration_names,
                                 )

            if these_commands:
                commands.extend(these_commands)

        return commands

    # ---------------------------------------------------------------------------
    
    return Impl.GenerateCommands(Execute, environment, debug)

# ---------------------------------------------------------------------------
def _SetupBootstrap( environment, 
                     repository_root, 
                     customization_mod, 
                     debug,
                     optional_configuration_names,
                     search_depth=5,
                   ):
    # ---------------------------------------------------------------------------
    def EnumerateDirectories():
        
        # ---------------------------------------------------------------------------
        def Impl(dir, fullpath_to_skip=None):
            """\
            Assumes that the repositories are siblings of each other. Searches begin in
            sibling dirs, then move up in the directory tree if the values are not found.
            """
        
            if environment.Name == "Windows":
                # If this is the first time through the loop, ensure that the drive letter
                # in the generated results is uppercase.
                if fullpath_to_skip == None:
                    drive, remainder = os.path.splitdrive(dir)
                        
                    if drive[-1] == ':':
                        drive = drive[:-1]

                    dir = "{}:{}".format(drive.upper(), remainder)

                # Don't count the slash that follows the drive name
                search_depth_offset = -1
                dir_comparison_decorator = lambda dir: dir.lower()
            else:
                search_depth_offset = 0
                dir_comparison_decorator = lambda dir: dir

            search_depth_offset -= repository_root.count(os.path.sep)
    
            # Perform a breadth-first search on the directories
            priority_search_items = [ dir, ]
            standard_search_items = []
            
            while priority_search_items or standard_search_items:
                if priority_search_items:
                    search_item = priority_search_items.pop(0)
                else:
                    search_item = standard_search_items.pop(0)

                assert os.path.isdir(search_item), search_item

                if os.path.exists(os.path.join(search_item, SourceRepositoryTools.IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME)):
                    continue

                if search_item.count(os.path.sep) + search_depth_offset >= search_depth:
                    continue

                yield search_item

                # Add children to the list of items to search
                try:
                    # Favor items with code-related keywords to help in the overall search perf
                    for item in os.listdir(search_item):
                        if dir_comparison_decorator(os.path.join(search_item, item)) == dir_comparison_decorator(fullpath_to_skip):
                            continue

                        fullpath = os.path.join(search_item, item)
                        if not os.path.isdir(fullpath):
                            continue

                        if item.lower() in [ "generated",
                                             ".hg",
                                           ]:
                            continue

                        is_code_related = False

                        fullpath_lower = fullpath.lower()

                        for name in [ "code",
                                      "coding",
                                      "source",
                                      "development",
                                    ]:
                            if name in fullpath_lower:
                                is_code_related = True
                                break

                        (priority_search_items if is_code_related else standard_search_items).append(fullpath)

                except:
                    # Most likely a permissions error raised when we attempted to
                    # access the dir. Unfortunately, there isn't a consistent exception
                    # type to catch across different operating systems.
                    pass        
            
            # Move up a directory
            parent, name = os.path.split(dir)
            if parent == dir:
                return

            for item in Impl(parent, dir):
                yield item

        # ---------------------------------------------------------------------------
        
        # Get a list of items to include in the search
        search_items = [ repository_root, ]

        # Search for additional drives on Windows
        if environment.Name == "Windows":
            import win32api
            import win32file

            this_drive = os.path.splitdrive(repository_root)[0].upper()
            assert not this_drive.endswith(os.path.sep)
            this_drive += os.path.sep

            drives = [ drive.upper() for drive in win32api.GetLogicalDriveStrings().split("\000") if drive and win32file.GetDriveType(drive) == win32file.DRIVE_FIXED ]
            drives.remove(this_drive)

            search_items.extend(drives)

        for search_item in search_items:
            for item in Impl(search_item):
                yield item

    # ---------------------------------------------------------------------------
    def CreateGuidLookupObject(name):
        return QuickObject( name=name,
                            repository_root=None,       # populated later
                          )

    # ---------------------------------------------------------------------------
    
    # Get the configurations
    configurations = None
    is_tool_repository = False

    if customization_mod:
        dependencies_func = getattr(customization_mod, CUSTOM_DEPENDENCIES_METHOD_NAME, None)
        if dependencies_func != None:
            configurations = dependencies_func()
            if configurations and not isinstance(configurations, dict):
                configurations = { None : configurations, }

            # Is this a tool repo
            if ( hasattr(dependencies_func, "_self_wrapper") and
                 dependencies_func._self_wrapper.func_name == "ToolRepository"
               ):
                is_tool_repository = True

    if not configurations:
        configurations = { None : SourceRepositoryTools.Configuration(),
                         }

    # A tool repository cannot have any configurations, dependencies, or version specs
    if ( is_tool_repository and 
         ( len(configurations) != 1 or 
           configurations.values()[0].Dependencies or 
           configurations.values()[0].VersionSpecs.Tools or 
           configurations.values()[0].VersionSpecs.Libraries
         )
       ):
        raise Exception("A tool repository cannot have any dependencies or version specs")

    # Calculate all of the repositories that we need to find
    fundamental_name, fundamental_guid = Impl.GetRepositoryUniqueId(SourceRepositoryTools.DE_FUNDAMENTAL)
    
    id_lookup = OrderedDict([ ( fundamental_guid, CreateGuidLookupObject(fundamental_name) ),
                            ])
                  
    if optional_configuration_names:
        for configuration_name in configurations.keys():
            if configuration_name not in optional_configuration_names:
                del configurations[configuration_name]

    for configuration_info in configurations.values():
        for dependency_info in configuration_info.Dependencies:
            if dependency_info.Id not in id_lookup:
                id_lookup[dependency_info.Id] = CreateGuidLookupObject(dependency_info.FriendlyName)

    sys.stdout.write(textwrap.dedent(
        """\

        Your system will be scanned for {num} {repositories}:
        {values}


        """).format( num=len(id_lookup),
                     repositories="repositories" if len(id_lookup) > 1 else "repository",
                     values='\n'.join([ "  - {} ({})".format(v.name, k) for k, v in id_lookup.iteritems() ]),
                   ))

    # Find them all
    remaining_repos = len(id_lookup)

    for directory in EnumerateDirectories():
        if debug:
            sys.stdout.write("Searching in '{}'\n".format(directory))

        result = Impl.GetRepositoryUniqueId(directory, throw_on_error=False)
        if result == None:
            continue

        repo_name, repo_guid = result

        if repo_guid in id_lookup:
            # Note that we may already have a repository associated with this repo. This can happen
            # when the repo was found near the originating repository and the search as continued into 
            # other directories.
            if not id_lookup[repo_guid].repository_root:
                id_lookup[repo_guid].repository_root = directory

                remaining_repos -= 1
                if not remaining_repos:
                    break

    if remaining_repos:
        unknown_repos = []

        for repo_guid, lookup_info in id_lookup.iteritems():
            if lookup_info.repository_root == None:
                unknown_repos.append(QuickObject( name=lookup_info.name,
                                                  guid=repo_guid,
                                                ))

        assert unknown_repos
        raise Exception(textwrap.dedent(
            """\
            Unable to find the {repository}:
                - {repos}
            """).format( repository="repository" if len(unknown_repos) == 1 else "repositories",
                         repos="\n    - ".join([ "{} ({})".format(unknown_repo.name, unknown_repo.guid) for unknown_repo in unknown_repos ]),
                       ))
    
    sys.stdout.write(textwrap.dedent(
        """\
        {num} {repositories} {were} found at {these} {locations}:
        {value}


        """).format( num=len(id_lookup),
                     repositories="repositories" if len(id_lookup) > 1 else "repository",
                     were="were" if len(id_lookup) > 1 else "was",
                     these="these" if len(id_lookup) > 1 else "this",
                     locations="locations" if len(id_lookup) > 1 else "location",
                     value='\n'.join([ "  - {0:<60}  : {1}".format("{} ({})".format(lookup_info.name, repo_guid), lookup_info.repository_root) for repo_guid, lookup_info in id_lookup.iteritems() ]),
                   ))

    # Create enhanced information based on the info we have available
    enhanced_configurations = OrderedDict()

    for configuration_name, configuration in configurations.iteritems():
        added_fundamental = False

        enhanced_dependencies = []

        for dependency in configuration.Dependencies:
            enhanced_dependencies.append(_EnhancedDependency(dependency, id_lookup[dependency.Id].repository_root))

            if dependency.Id == fundamental_guid:
                added_fundamental = True

        # We need to add the fundamental repo as a dependency unless one
        # of the following conditions are met.
        if ( not added_fundamental and
             repository_root != id_lookup[fundamental_guid].repository_root and 
             not is_tool_repository
           ):
            enhanced_dependencies.append(_EnhancedDependency( SourceRepositoryTools.Dependency(fundamental_guid, fundamental_name),
                                                              SourceRepositoryTools.DE_FUNDAMENTAL,
                                                            ))

        enhanced_configurations[configuration_name] = _EnhancedConfiguration( enhanced_dependencies,
                                                                              configuration.VersionSpecs,
                                                                              Impl.RepositoryInformation.CalculateFingerprint( [ repository_root, ] + [ di.RepositoryRoot for di in enhanced_dependencies ],
                                                                                                                               repository_root,
                                                                                                                             ),
                                                                            )

    # Get the python binary. Note that we can't use the binary that invoked this
    # file, as we may have installed a new version.
    python_binary = SourceRepositoryTools.GetVersionedDirectory( [], # Always get the latest version
                                                                 SourceRepositoryTools.DE_FUNDAMENTAL,
                                                                 "Tools",
                                                                 "Python",
                                                               )

    potential_binary = os.path.join(python_binary, "bin")
    if os.path.isdir(potential_binary):
        python_binary = potential_binary

    python_binary = os.path.join(python_binary, "python")

    potential_binary = "{}{}".format(python_binary, environment.ExecutableExtension)
    if os.path.isfile(potential_binary):
        python_binary = potential_binary

    assert os.path.isfile(python_binary), python_binary

    # Write the bootstrap data
    Impl.RepositoryInformation( python_binary,                                SourceRepositoryTools.DE_FUNDAMENTAL,
                                is_tool_repository,
                                enhanced_configurations,
                              ).Save(repository_root)

# ---------------------------------------------------------------------------
def _SetupCustom(environment, repository_root, customization_mod, debug, optional_configuration_names):
    if customization_mod == None or not hasattr(customization_mod, CUSTOM_ACTIONS_METHOD_NAME):
        return

    if customization_mod.CustomActions.func_code.co_argcount == 0:
        return customization_mod.CustomActions()
    elif customization_mod.CustomActions.func_code.co_argcount == 1:
        return customization_mod.CustomActions(optional_configuration_names)

    raise Exception("'{}' in '{}' should take 0..1 paramters".format(CUSTOM_ACTIONS_METHOD_NAME, inspect.getsourcefile(customization_mod)))

# ---------------------------------------------------------------------------
def _SetupShortcuts(environment, repository_root, customization_mod, debug, optional_configuration_names):
    script_name = environment.CreateScriptName(SourceRepositoryTools.ACTIVATE_ENVIRONMENT_NAME)

    shortcut_dest = os.path.join(SourceRepositoryTools.DE_FUNDAMENTAL, "SourceRepositoryTools", "Impl", script_name)
    assert os.path.isfile(shortcut_dest), shortcut_dest

    return [ Shell.SymbolicLink( os.path.join(repository_root, script_name),
                                 shortcut_dest,
                               ),
           ]

# ---------------------------------------------------------------------------
def _SetupGenerated(environment, repository_root, customization_mod, debug, optional_configuration_names):
    generated_dir = os.path.join(repository_root, SourceRepositoryTools.GENERATED_DIRECTORY_NAME)
    assert os.path.isdir(generated_dir), generated_dir
    
    os.chmod(generated_dir, 0x777)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
