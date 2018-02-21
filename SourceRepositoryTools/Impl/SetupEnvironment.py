# ----------------------------------------------------------------------
# |  
# |  SetupEnvironment.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 12:59:02
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import configparser
import json
import os
import shutil
import sys
import textwrap

from collections import OrderedDict

import six

import SourceRepositoryTools
from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl.Configuration import Configuration, Dependency
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl.EnvironmentBootstrap import EnvironmentBootstrap
from SourceRepositoryTools.Impl import Utilities

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
CODE_DIRECTORY_NAMES                        = [ "code",
                                                "coding",
                                                "source",
                                                "src",
                                                "development",
                                                "develop",
                                                "dev",
                                              ]

ENUMERATE_EXCLUDE_DIRS                      = [ "generated",
                                                ".hg",
                                                ".git",
                                              ]

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Filename for generated content or standard output if the value is 'stdout'"),
                                                  repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Root of the repository"),
                                                  debug=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Display debug information"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.ArgumentInfo("Configurations to setup; all will be setup if explicit values are not provided"),
                                                )
@CommonEnvironmentImports.CommandLine.FunctionConstraints( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                           repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                           configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(arity='*'),
                                                         )
def EntryPoint( output_filename_or_stdout,
                repository_root,
                debug=False,
                configuration=None,
              ):
    configurations = configuration or []; del configuration
    environment = CommonEnvironmentImports.Shell.GetEnvironment()

    # Get the setup customization module
    potential_customization_filename = os.path.join(repository_root, Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)
    if os.path.isfile(potential_customization_filename):
        customization_name = os.path.splitext(Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)[0]

        sys.path.insert(0, repository_root)
        customization_mod = __import__(customization_name)
        del sys.path[0]

    else:
        customization_mod = None

    # ----------------------------------------------------------------------
    def Execute():
        commands = []

        for func in [ _SetupBootstrap,
                      _SetupCustom,
                      _SetupShortcuts,
                      _SetupGeneratedPermissions,
                      _SetupScmHooks,
                    ]:
            these_commands = func( environment,
                                   repository_root,
                                   customization_mod,
                                   debug,
                                   configurations,
                                  )
            if these_commands:
                commands += these_commands

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
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _SetupBootstrap( environment,
                     repository_root,
                     customization_mod,
                     debug,
                     configurations_to_setup,
                     search_depth=5,
                   ):
    # Look for all dependencies by intelligently enumerating through the file system

    search_depth += repository_root.count(os.path.sep)
    if environment.CategoryName == "Windows":
        # Remove the slash associated with the drive name
        assert search_depth
        search_depth -= 1

    fundamental_repo = SourceRepositoryTools.GetFundamentalRepository()

    repository_root_dirname = os.path.dirname(repository_root)
    len_repository_root_dirname = len(repository_root_dirname)

    # ----------------------------------------------------------------------
    class LookupObject(object):
        def __init__(self, name):
            self.Name                       = name
            self.repository_root            = None
            self.dependent_configurations   = []

    # ----------------------------------------------------------------------
    def EnumerateDirectories():
        search_items = []
        searched_items = set()

        # ----------------------------------------------------------------------
        def FirstNonmatchingChar(s):
            for index, c in enumerate(s):
                if ( index == len_repository_root_dirname or 
                     c != repository_root_dirname[index]
                   ):
                    break

            return index

        # ----------------------------------------------------------------------
        def PushSearchItem(item):
            item = os.path.realpath(os.path.normpath(item))

            parts = item.split(os.path.sep)
            if len(parts) > search_depth:
                return

            parts_lower = set([ part.lower() for part in parts ])

            priority = 1
            for bump_name in CODE_DIRECTORY_NAMES:
                if bump_name in parts_lower:
                    priority = 0
                    break

            # Every item excpet the last is used for sorting
            search_items.append(( -FirstNonmatchingChar(item),              # Favor parents over other locations
                                  priority,                                 # Favor higer priorty items
                                  len(parts),                               # Favor dirs closer to the root
                                  item.lower(),                             # Case insensitive sort
                                  item,
                                ))

            search_items.sort()

        # ----------------------------------------------------------------------
        def PopSearchItem():
            return search_items.pop(0)[-1]

        # ----------------------------------------------------------------------
        def Impl( skip_root,
                  preprocess_item_func=None,            # def Func(item) -> item
                ):
            preprocess_item_func = preprocess_item_func or (lambda item: item)

            while search_items:
                search_item = PopSearchItem()

                # Don't process if the dir has already been processed
                if search_item in searched_items:
                    continue

                searched_items.add(search_item)

                # Don't process if the dir doesn't exist anymore (these searches can take
                # ahwile and dirs come and go)
                if not os.path.isdir(search_item):
                    continue

                # Don't process if the dir has been explicitly ignored
                if os.path.exists(os.path.join(search_item, Constants.IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME)):
                    continue

                yield search_item

                try:
                    # Add the parent to the queue
                    potential_parent = os.path.dirname(search_item)
                    if potential_parent != search_item:
                        if not skip_root or os.path.dirname(potential_parent) != potential_parent:
                            PushSearchItem(preprocess_item_func(potential_parent))

                    # Add the children to the queue
                    for item in os.listdir(search_item):
                        fullpath = os.path.join(search_item, item)
                        if not os.path.isdir(fullpath):
                            continue

                        if item.lower() in ENUMERATE_EXCLUDE_DIRS:
                            continue

                        PushSearchItem(preprocess_item_func(fullpath))

                except PermissionError:
                    # Most likely a permissions error raised when we attempted to
                    # access the dir. Unfortunately, there isn't a consistent exception
                    # type to catch across different platforms.
                    pass

        # ----------------------------------------------------------------------

        PushSearchItem(repository_root)

        if environment.CategoryName == "Windows":
            # ----------------------------------------------------------------------
            def ItemPreprocessor(item):
                drive, remainder = os.path.splitdrive(item)
                if drive[-1] == ':':
                    drive = drive[:-1]

                return "{}:{}".format(drive.upper(), remainder)

            # ----------------------------------------------------------------------

            for item in Impl(True, ItemPreprocessor):
                yield item

            # If here, look at other drive locations
            import win32api
            import win32file

            for drive in [ drive for drive in win32api.GetLogicalDriveStrings().split('\000') if drive and win32file.GetDriveType(drive) == win32file.DRIVE_FIXED ]:
                PushSearchItem(drive)

            for item in Impl(False, ItemPreprocessor):
                yield item

        else:
            for item in Impl(False):
                yield item

    # ----------------------------------------------------------------------

    # Get the configurations from the script
    configurations = None
    is_tool_repository = False

    if customization_mod:
        dependencies_func = getattr(customization_mod, Constants.SETUP_ENVIRONMENT_DEPENDENCIES_METHOD_NAME, None)
        if dependencies_func is not None:
            # Get custom configurations
            configurations = dependencies_func()

            if configurations and not isinstance(configurations, dict):
                configurations = { None : configurations }

            # Is this a tool repo? Tool repos are specified via
            # the ToolRepository wrapt decorator.
            if ( hasattr(dependencies_func, "_self_wrapper") and
                 dependencies_func._self_wrapper.__name__ == "ToolRepository"
               ):
                is_tool_repository = True

    if not configurations:
        configurations = { None : Configuration(),
                         }

    has_configurations = len(configurations) > 1 or next(six.iterkeys(configurations)) is not None

    # A tool repository cannot have configurations, dependencies, or version specs
    if ( is_tool_repository and
         ( has_configurations or
           next(six.itervalues(configurations)).Dependencies or
           next(six.itervalues(configurations)).VersionSpecs.Tools or
           next(six.itervalues(configurations)).VersionSpecs.Libraries
         )
       ):
        raise Exception("A tool repository cannot not have any configurations, dependencies, or version specs.")

    # Calculate all of the repositories that we need to find
    if configurations_to_setup:
        for config_name in list(six.iterkeys(configurations)):
            if config_name not in configurations_to_setup:
                del configurations[config_name]

    # Create a repo lookup list
    fundamental_name, fundamental_guid = Utilities.GetRepositoryUniqueId(fundamental_repo)

    id_lookup = OrderedDict([ ( fundamental_guid, LookupObject(fundamental_name) ),
                            ])

    for config_name, config_info in six.iteritems(configurations):
        for dependency_info in config_info.Dependencies:
            if dependency_info.Id not in id_lookup:
                id_lookup[dependency_info.Id] = LookupObject(dependency_info.FriendlyName)

            id_lookup[dependency_info.Id].dependent_configurations.append(config_name)

    # Display status
    col_sizes = [ 40, 32, 100, ]
    display_template = "{{name:<{0}}}  {{guid:<{1}}}  {{data:<{2}}}".format(*col_sizes)

    max_config_name_length = int(col_sizes[0] * 0.75)
    config_display_info = []

    for config_name, config_info in six.iteritems(configurations):
        if config_name is None:
            continue

        max_config_name_length = max(max_config_name_length, len(config_name))
        config_display_info.append(( config_name, config_info.Description ))

    sys.stdout.write(textwrap.dedent(
        """\

        Your system will be scanned for these repositories

            {header}
            {sep}
            {values}

            {configurations}

        """).format( header=display_template.format( name="Repository Name",
                                                     guid="Id",
                                                     data="Dependent Configurations",
                                                   ),
                     sep=display_template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ],
                                                                                      [ '-' * col_size for col_size in col_sizes ],
                                                                                    ) }),
                     values=CommonEnvironmentImports.StreamDecorator.LeftJustify( '\n'.join([ display_template.format( name=v.Name,
                                                                                                                       guid=k,
                                                                                                                       data=', '.join(sorted([ dc for dc in v.dependent_configurations if dc], key=str.lower)),
                                                                                                                     )
                                                                                              for k, v in six.iteritems(id_lookup)
                                                                                            ]),
                                                                                  4,
                                                                                ),
                     configurations=CommonEnvironmentImports.StreamDecorator.LeftJustify( '' if not has_configurations else textwrap.dedent(
                                                                                            """\
                                                                                            Based on these configurations:

                                                                                                {}
                                                                                                {}
                                                                                            """).format( CommonEnvironmentImports.StreamDecorator.LeftJustify( '\n'.join([ "- {0:<{1}}{2}".format( config_name,
                                                                                                                                                                                                   max_config_name_length,
                                                                                                                                                                                                   " : {}".format(description) if description else '',
                                                                                                                                                                                                 )
                                                                                                                                                                           for config_name, description in config_display_info
                                                                                                                                                                         ]),
                                                                                                                                                               4,
                                                                                                                                                             ),
                                                                                                         CommonEnvironmentImports.StreamDecorator.LeftJustify( '' if configurations_to_setup else textwrap.dedent(
                                                                                                                                                                    """\

                                                                                                                                                                    To setup specific configurations, specify this argument one or more times on the command line:

                                                                                                                                                                        /configuration=<configuration name>
                                                                                                                                                                    """),
                                                                                                                                                               4,
                                                                                                                                                             ),
                                                                                                                            
                                                                                                       ),
                                                                                          4,
                                                                                        ),
                   ))

    # Find them all
    remaining_repos = len(id_lookup)

    for directory in EnumerateDirectories():
        if debug:
            sys.stdout.write("Searching in '{}'\n".format(directory))

        result = Utilities.GetRepositoryUniqueId( directory, 
                                                  find_by_scm=False,
                                                  throw_on_error=False,
                                                )
        if result is None:
            continue

        repo_name, repo_guid = result

        if repo_guid in id_lookup:
            # Note that we may already have a repository associated with this repo. This can
            # happen when the repo was found near the originating repository and the search has
            # continued into other directories.
            if id_lookup[repo_guid].repository_root is None:
                id_lookup[repo_guid].repository_root = directory

                remaining_repos -= 1
                if not remaining_repos:
                    break

    if remaining_repos:
        unknown_repos = []

        for repo_guid, lookup_info in six.iteritems(id_lookup):
            if lookup_info.repository_root is None:
                unknown_repos.append(( lookup_info.name, repo_guid ))

        assert unknown_repos
        raise Exception(textwrap.dedent(
            """\
            Unable to find the {repository}:
            {repos}
            """).format( repository="repository" if len(unknown_repos) == 1 else "repositories",
                         repos='\n'.join([ "    - {} ({})".format(repo_name, repo_guid) for repo_name, repo_guid in unknown_repos ]),
                       ))

    sys.stdout.write(textwrap.dedent(
        """\
        {num} {repository} {was} found at {this} {location}:

            {header}
            {sep}
            {values}

        
        
        """).format( num=len(id_lookup),
                     repository="repository" if len(id_lookup) == 1 else "repositories",
                     was="was" if len(id_lookup) == 1 else "were",
                     this="this" if len(id_lookup) == 1 else "these",
                     location="location" if len(id_lookup) == 1 else "locations",
                     header=display_template.format( name="Repository Name",
                                                     guid="Id",
                                                     data="Location",
                                                   ),
                     sep=display_template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ],
                                                                                      [ '-' * col_size for col_size in col_sizes ],
                                                                                    ) }),
                     values=CommonEnvironmentImports.StreamDecorator.LeftJustify( '\n'.join([ display_template.format( name=lookup_info.Name,
                                                                                                                       guid=repo_guid,
                                                                                                                       data=lookup_info.repository_root,
                                                                                                                     )
                                                                                              for repo_guid, lookup_info in six.iteritems(id_lookup)
                                                                                            ]),
                                                                                  4,
                                                                                ),
                   ))

    # Update the provided configuration info with information that we have discovered
    for config_name, config_info in six.iteritems(configurations):
        added_fundamental = False

        for dependency in config_info.Dependencies:
            dependency.RepositoryRoot = id_lookup[dependency.Id].repository_root
            
            if dependency.Id == fundamental_guid:
                added_fundamental = True

        # We need to add the fundamental repo as a dependency unless one
        # of the following conditions are met.
        if ( not added_fundamental and
             repository_root != id_lookup[fundamental_guid].repository_root and
             not is_tool_repository
           ):
            config_info.Dependencies.append(Dependency(fundamental_guid, fundamental_name))
            config_info.Dependencies[-1].RepositoryRoot = fundamental_repo

        config_info.Fingerprint = Utilities.CalculateFingerprint( [ repository_root, ] + [ dependency.RepositoryRoot for dependency in config_info.Dependencies ],
                                                                  repository_root,
                                                                )

    # Get the latest python binary, which may be different than the binary used to launch
    # this process.
    python_binary = Utilities.GetVersionedDirectory( [], # Always get the latest
                                                     fundamental_repo,
                                                     Constants.TOOLS_SUBDIR,
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

    # Write the bootstrap files
    EnvironmentBootstrap( python_binary,
                          fundamental_repo,
                          is_tool_repository,
                          has_configurations,
                          configurations,
                        ).Save( repository_root,
                                environment=environment,
                              )

# ----------------------------------------------------------------------
def _SetupCustom( environment,
                  repository_root,
                  customization_mod,
                  debug,
                  configurations,
                ):
    if customization_mod is None or not hasattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME):
        return

    func = CommonEnvironmentImports.Interface.CreateCulledCallable(getattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME))

    return func({ "debug" : debug,
                  "configurations" : configurations,
                })

# ----------------------------------------------------------------------
def _SetupShortcuts( environment,
                     repository_root,
                     customization_mod,
                     debug,
                     configurations,
                   ):
    activate_script = environment.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME)

    shortcut_dest = os.path.join(SourceRepositoryTools.GetFundamentalRepository(), "SourceRepositoryTools", "Impl", activate_script)
    assert os.path.isfile(shortcut_dest), shortcut_dest

    return [ environment.SymbolicLink(os.path.join(repository_root, activate_script), shortcut_dest),
           ]

# ----------------------------------------------------------------------
def _SetupGeneratedPermissions( environment,
                                repository_root,
                                customization_mod,
                                debug,
                                configurations,
                              ):
    generated_dir = os.path.join(repository_root, Constants.GENERATED_DIRECTORY_NAME, environment.CategoryName)
    assert os.path.isdir(generated_dir), generated_dir

    os.chmod(generated_dir, 0x777)

# ----------------------------------------------------------------------
def _SetupScmHooks( environment,
                    repository_root,
                    customization_mod,
                    debug,
                    configurations,
                  ):
    # Mercurial
    if os.path.isdir(os.path.join(repository_root, ".hg")):
        hooks_filename = os.path.normpath(os.path.join(_script_dir, "Hooks", "Mercurial.py"))
        assert os.path.isfile(hooks_filename), hooks_filename

        config = configparser.ConfigParser( allow_no_value=True,
                                          )

        potential_hg_filename = os.path.join(repository_root, ".hg", "hgrc")
        if os.path.isfile(potential_hg_filename):
            with open(potential_hg_filename) as f:
                config.read_file(f)

        if not config.has_section("hooks"):
            config.add_section("hooks")

        config.set("hooks", "pretxncommit.CommonEnvironment", "python:{}:PreTxnCommit".format(hooks_filename))
        config.set("hooks", "preoutgoing.CommonEnvironment", "python:{}:PreOutgoing".format(hooks_filename))
        config.set("hooks", "pretxnchangegroup.CommonEnvironment", "python:{}:PreTxnChangeGroup".format(hooks_filename))

        backup_hg_filename = "{}.bak".format(potential_hg_filename)
        if os.path.isfile(potential_hg_filename) and not os.path.isfile(backup_hg_filename):
            shutil.copyfile(potential_hg_filename, backup_hg_filename)

        with open(potential_hg_filename, 'w') as f:
            config.write(f)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt: pass