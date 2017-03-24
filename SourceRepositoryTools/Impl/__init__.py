# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/09/2015 03:25:27 PM
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
import hashlib
import os
import re
import sys
import textwrap

from collections import OrderedDict

import six
from six.moves import cPickle as pickle
from six.moves import StringIO

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

import CommonEnvironmentImports

with CommonEnvironmentImports.Package.NameInfo(__package__) as ni:
    __package__ = ni.created

    from .. import Constants

    __package__ = ni.original

SourceRepositoryTools                       = CommonEnvironmentImports.Package.ImportInit("..")

# ----------------------------------------------------------------------
Shell                                       = CommonEnvironmentImports.Shell
StreamDecorator                             = CommonEnvironmentImports.StreamDecorator

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
REPOSITORY_ID_CONTENT_TEMPLATE              = textwrap.dedent(
    """\
    This file is used to uniquely identify this repository for the purposes of dependency management.
    Other repositories that depend on this one will intelligently search for this file upon initial
    setup and generate information that can be used when activating development environments.
    
    **** PLEASE DO NOT MODIFY, REMOVE, OR RENAME THIS FILE, AS DOING SO WILL LIKELY BREAK OTHER REPOSITORIES! ****
    
    Friendly Name:      {name}
    GUID:               {guid}
    """)

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class RepositoryInformation(object):

    _Load_regex = None

    # ---------------------------------------------------------------------------
    @classmethod
    def Load(cls, repository_root):
        environment = Shell.GetEnvironment()

        filename = os.path.join(repository_root, Constants.GENERATED_DIRECTORY_NAME, environment.CategoryName, Constants.GENERATED_BOOTSTRAP_FILENAME)
        if not os.path.isfile(filename):
            raise Exception("The filename '{}' does not exist; please run '{}' and try again.".format(filename, os.path.join(repository_root, "{}{}".format(Constants.SETUP_ENVIRONMENT_NAME, environment.ScriptExtension))))

        if cls._Load_regex == None:
            cls._Load_regex = CommonEnvironmentImports.RegularExpression.TemplateStringToRegex(cls._BOOTSTRAP_CONTENT_TEMPLATE)

        match = cls._Load_regex.match(open(filename).read())
        if not match:
            raise Exception("The content in '{}' appears to be corrupt.".format(filename))

        python_binary = CommonEnvironmentImports.FileSystem.Normalize(os.path.join(repository_root, match.group("python_binary")))
        fundamental_development_root = CommonEnvironmentImports.FileSystem.Normalize(os.path.join(repository_root, match.group("fundamental_development_root")))
        is_tool_repository = match.group("is_tool_repository") == '1'
        is_configurable_repository = match.group("is_configurable_repository") == '1'

        # The SetupEnvironmnet model must be defined in sys.modules to de-pickle without
        # error.
        if "SetupEnvironment" not in sys.modules:
            global __package__
            
            with CommonEnvironmentImports.Package.NameInfo(__package__) as ni:
                __package__ = ni.created
            
                from . import SetupEnvironment
                
                __package__ = ni.original
            
            sys.modules["SetupEnvironment"] = SetupEnvironment
            
            # ---------------------------------------------------------------------------
            def SetupEnvironmentCleanup():
                del sys.modules["SetupEnvironment"]

            # ---------------------------------------------------------------------------
        else:
            # ---------------------------------------------------------------------------
            def SetupEnvironmentCleanup():
                pass

            # ---------------------------------------------------------------------------

        with CommonEnvironmentImports.CallOnExit(SetupEnvironmentCleanup):
            configurations = pickle.loads(CommonEnvironmentImports.six_plus.BytesFromString(match.group("configurations"), decode=True)) or {}

        for configuration in configurations.values():
            for dependency in configuration.Dependencies:
                # Sometimes, a value that should be None is pickled as a string. Ensure that
                # None is None.
                if not dependency.Configuration:
                    dependency.Configuration = None

                dependency.RepositoryRoot = CommonEnvironmentImports.FileSystem.Normalize(os.path.join(repository_root, dependency.RepositoryRoot))

            new_fingerprint = OrderedDict()

            for k, v in six.iteritems(configuration.Fingerprint):
                new_fingerprint[CommonEnvironmentImports.FileSystem.Normalize(os.path.join(repository_root, k))] = v

            configuration.Fingerprint = new_fingerprint
            
        return cls( python_binary,
                    fundamental_development_root,
                    is_tool_repository,
                    configurations,
                    repository_root=CommonEnvironmentImports.FileSystem.Normalize(repository_root),
                  )

    # ---------------------------------------------------------------------------
    @staticmethod
    def CalculateFingerprint(repository_dirs, relative_root=None):
        results = OrderedDict()

        for repository_dir in repository_dirs:
            md5 = hashlib.md5()

            filename = os.path.join(repository_dir, "{}.py".format(Constants.SETUP_ENVIRONMENT_NAME))
            if os.path.isfile(filename):
                with open(filename) as f:
                    in_file_header = True

                    # Skip the file header, as it has no impact on the file's actual contents
                    for line in f:
                        if in_file_header and line.lstrip().startswith('#'):
                            continue

                        in_file_header = False
                        md5.update(line)

            if relative_root:
                repository_dir = CommonEnvironmentImports.FileSystem.GetRelativePath(relative_root, repository_dir)

            results[repository_dir] = md5.hexdigest()

        return results

    # ---------------------------------------------------------------------------
    def __init__( self,
                  python_binary,
                  fundamental_development_root,
                  is_tool_repository,
                  configurations,
                  repository_root=None,
                ):
        assert os.path.isfile(python_binary), python_binary
        assert os.path.isdir(fundamental_development_root), fundamental_development_root
        
        self.python_binary                  = python_binary
        self.fundamental_development_root   = fundamental_development_root
        self.is_tool_repository             = is_tool_repository
        self.configurations                 = configurations or {}
        self.repository_root                = repository_root or ''

    # ---------------------------------------------------------------------------
    @property
    def IsConfigurable(self):
        return len(self.configurations) > 1 or None not in self.configurations
    
    # ---------------------------------------------------------------------------
    @property
    def IsToolRepository(self):
        return self.is_tool_repository

    # ---------------------------------------------------------------------------
    @property
    def Configurations(self):
        if not self.IsConfigurable:
            return

        return self.configurations.keys()

    # ---------------------------------------------------------------------------
    def Save(self, repository_root):
        generated_dir = os.path.join(repository_root, Constants.GENERATED_DIRECTORY_NAME)
        if not os.path.isdir(generated_dir):
            os.makedirs(generated_dir)

        # Ensure that we save everything as a relative path
        python_binary = CommonEnvironmentImports.FileSystem.GetRelativePath(repository_root, self.python_binary)
        fundamental_development_root = CommonEnvironmentImports.FileSystem.GetRelativePath(repository_root, self.fundamental_development_root)

        configurations = copy.deepcopy(self.configurations)
        for configuration in configurations.values():
            for dependency in configuration.Dependencies:
                dependency.RepositoryRoot = CommonEnvironmentImports.FileSystem.GetRelativePath(repository_root, dependency.RepositoryRoot)

        filename = os.path.join(generated_dir, Shell.GetEnvironment().CategoryName, Constants.GENERATED_BOOTSTRAP_FILENAME)
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
            
        with open(filename, 'w') as f:
            f.write(self._BOOTSTRAP_CONTENT_TEMPLATE.format( python_binary=python_binary,
                                                             fundamental_development_root=fundamental_development_root,
                                                             is_tool_repository="1" if self.IsToolRepository else "0",
                                                             is_configurable_repository="1" if self.IsConfigurable else "0",
                                                             configurations=CommonEnvironmentImports.six_plus.BytesToString(pickle.dumps(configurations), encode=True),
                                                           ))

    # ---------------------------------------------------------------------------
    # Note that this format is designed to be easily parsed by batch/script files;
    # it is not formatted to look pretty.
    _BOOTSTRAP_CONTENT_TEMPLATE = textwrap.dedent(
        """\
        python_binary={python_binary}
        fundamental_development_root={fundamental_development_root}

        is_tool_repository={is_tool_repository}
        is_configurable_repository={is_configurable_repository}

        {configurations}
        """)

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
_GetRepositoryUniqueId_regex = None

def GetRepositoryUniqueId( repository_root, 
                           scm=None, 
                           throw_on_error=True,
                         ):
    global _GetRepositoryUniqueId_regex

    if _GetRepositoryUniqueId_regex == None:
        _GetRepositoryUniqueId_regex = CommonEnvironmentImports.RegularExpression.TemplateStringToRegex(REPOSITORY_ID_CONTENT_TEMPLATE)

    filename = os.path.join(repository_root, Constants.REPOSITORY_ID_FILENAME)
    if os.path.isfile(filename):
        match = _GetRepositoryUniqueId_regex.match(open(filename).read())
        if not match:
            raise Exception("The content in '{}' appears to be corrupt".format(filename))

        name = match.group("name")
        unique_id = match.group("guid").upper()
    else:
        if scm == None:
            scm or CommonEnvironmentImports.SourceControlManagement.GetSCM(repository_root, throw_on_error=False)
            if scm == None:
                if throw_on_error:
                    raise Exception("Id information was not found nor could SCM information be extracted from '{}'".format(repository_root))
                
                return None
            
        unique_id = scm.GetUniqueName(repository_root)
        name = unique_id

    return name, unique_id

# ---------------------------------------------------------------------------
def IsOSNameDirectory(path, subdirs=None):
    potential_os_names = { env.Name for env in Shell.GetPotentialEnvironments() }

    for os_name in [ Constants.AGNOSTIC_OS_NAME,
                     Constants.LINUX_OS_NAME,
                     "src",
                   ]:
        potential_os_names.add(os_name)

    return _IsImpl(path, potential_os_names, subdirs=subdirs)

# ---------------------------------------------------------------------------
def IsOSVersionDirectory(path, environment, subdirs=None):
    return _IsImpl(path, environment.PotentialOSVersionDirectoryNames, subdirs=subdirs)

# ---------------------------------------------------------------------------
def IsOSArchitectureDirectory(path, environment, subdirs=None):
    return _IsImpl(path, environment.PotentialOSArchitectureDirectoryNames, subdirs=subdirs)

# ---------------------------------------------------------------------------
def GenerateCommands( functor,              # def Func() -> []
                      environment,
                      is_debug,
                    ):
    """\
    Returns (rval, generated_commands)
    """

    assert functor
    assert environment

    commands = []

    try:
        result = functor()
        
        if isinstance(result, tuple):
            rval, commands = result
        else:
            commands = result
            rval = 0
    except:
        import traceback

        error = traceback.format_exc()

        commands = [ Shell.Message("ERROR: {}".format(StreamDecorator.LeftJustify(error, len("ERROR: ")))),
                     Shell.Exit( pause_on_error=True,
                                 return_code=1,
                               ),
                   ]
        rval = -1

    if is_debug:
        sink = StringIO()
        StreamDecorator(sink, line_prefix="Debug: ").write(environment.GenerateCommands(commands))
        sink = sink.getvalue()

        commands = [ Shell.Message("{}\n".format(sink)), ] + commands

    return rval, commands

# ---------------------------------------------------------------------------
def TraverseDependencies(repository_root, configuration):
    repository_root = CommonEnvironmentImports.FileSystem.Normalize(repository_root)
    assert os.path.isdir(repository_root), repository_root

    repositories = OrderedDict()
    
    tool_version_info = []
    library_version_info = {}
    version_info_lookup = {}

    # ---------------------------------------------------------------------------
    def CreateContext(root, configuration=None):
        name, id = GetRepositoryUniqueId(root)

        return CommonEnvironmentImports.QuickObject( id=id,
                                                     name=name,
                                                     root=root,
                                                     configuration=configuration,
                                                   )

    # ---------------------------------------------------------------------------
    def CreateVersionInfo(version, context):
        return CommonEnvironmentImports.QuickObject( version=version,
                                                     context=context,
                                                   )

    # ---------------------------------------------------------------------------
    def Walk( referencing_context,
              context,
              priority_modifier,
            ):
        if context.id not in repositories:
            repo_info = RepositoryInformation.Load(context.root)
            
            repo_info.context = context
            repo_info.referencing_context = referencing_context
            repo_info.priority_modifier = 0

            repositories[context.id] = repo_info
            
            recurse = True
        else:
            recurse = False

        repo_info = repositories[context.id]
        repo_info.priority_modifier += priority_modifier

        # Ensure that the configuration name is valid
        if repo_info.IsConfigurable and not context.configuration:
            raise Exception("The repository at '{}' is configurable, but a configuration name was not provided".format(context.root))

        if not repo_info.IsConfigurable and context.configuration:
            raise Exception("The repository at '{}' is not configurable, but the configuration name '{}' was provided".format(context.root, context.configuration))

        if context.configuration not in repo_info.configurations:
            raise Exception(textwrap.dedent(
                """\
                The configuration '{configuration}' is not a valid configuration for the repository at '{root}'.
                Valid configurations are:
                {configs}
                """).format( configuration=context.configuration,
                             root=context.root,
                             configs='\n'.join([ "    - {}".format(config or "<None>") for config in repo_info.configurations.keys() ]),
                           ))

        # Check for consistent locations
        if context.root != repo_info.context.root:
            raise Exception(textwrap.dedent(
                """\
                There was a mismatch in repository locations.

                Repository:                 {name} <{id}>

                New Location:               {new_value}
                Referenced By:              {new_name} <{new_id}> [{new_root}]

                Original Location:          {original_value}
                Referenced By:              {original_name} <{original_id}> [{original_root}]
                """).format( name=context.name,
                             id=context.id,
                             
                             new_value=context.root,
                             new_name=referencing_context.name,
                             new_id=referencing_context.id,
                             new_root=referencing_context.root,
                             
                             original_value=repo_info.context.root,
                             original_name=repo_info.referencing_context.name,
                             original_id=repo_info.referencing_context.id,
                             original_root=repo_info.referencing_context.root,
                           ))

        if context.configuration != repo_info.context.configuration:
            raise Exception(textwrap.dedent(
                """\
                There was a mismatch in repository configurations.

                Repository:                 {name} <{id}> [{root}]

                New Configuration:          {new_value}
                Referenced By:              {new_name} <{new_id}> [{new_root}]

                Original Configuration:     {original_value}
                Referenced By:              {original_name} <{original_id}> [{original_root}]
                """).format( name=context.name,
                             id=context.id,
                             root=context.root,
                             
                             new_value=context.configuration,
                             new_name=referencing_context.name,
                             new_id=referencing_context.id,
                             new_root=referencing_context.root,
                             
                             original_value=repo_info.context.configuration,
                             original_name=repo_info.referencing_context.name,
                             original_id=repo_info.referencing_context.id,
                             original_root=repo_info.referencing_context.root,
                           ))

        # Process the version info
        # ---------------------------------------------------------------------------
        def OnVersionMismatch(type_, version_info, existing_version_info):
            original_context = version_info_lookup[existing_version_info]

            raise Exception(textwrap.dedent(
                """\
                There was a mismatch in version information.

                Item:                   {name} <{type_}>

                New Version:            {new_value}
                Specified By:           {new_name} ({new_config}) <{new_id}> [{new_root}]

                Original Version:       {original_value}
                Specified By:           {original_name} ({original_config}) <{original_id}> [{original_root}]
                """).format( name=version_info.Name,
                             type_=type_,

                             new_value=version_info.Version,
                             new_name=context.name,
                             new_config=context.configuration,
                             new_id=context.id,
                             new_root=context.root,

                             original_value=existing_version_info.Version,
                             original_name=original_context.name,
                             original_config=original_context.configuration,
                             original_id=original_context.id,
                             original_root=original_context.root,
                           ))

        # ---------------------------------------------------------------------------
        
        for version_info in repo_info.configurations[context.configuration].VersionSpecs.Tools:
            existing_version_info = CommonEnvironment.Get(tool_version_info, lambda tvi: tvi.Name == version_info.Name)
            
            if existing_version_info == None:
                tool_version_info.append(version_info)
                version_info_lookup[version_info] = context
            
            elif version_info.Version != existing_version_info.Version:
                OnVersionMismatch("Tools", version_info, existing_version_info)

        for library_language, version_info_items in six.iteritems(repo_info.configurations[context.configuration].VersionSpecs.Libraries):
            for version_info in version_info_items:
                existing_version_info = CommonEnvironment.Get(library_version_info.get(library_language, []), lambda lvi: lvi.Name == version_info.Name)

                if existing_version_info == None:
                    library_version_info.setdefault(library_language, []).append(version_info)
                    version_info_lookup[version_info] = context

                elif version_info.Version != existing_version_info.Version:
                    OnVersionMismatch("{} Libraries".format(library_language), version_info, existing_version_info)

        # Process this repository's dependencies
        if recurse:
            for dependency_info in repo_info.configurations[context.configuration].Dependencies:
                dependency_context = CreateContext(dependency_info.RepositoryRoot, dependency_info.Configuration)
                Walk(context, dependency_context, priority_modifier + 1)

    # ---------------------------------------------------------------------------
    
    Walk(None, CreateContext(repository_root, configuration), 1)
    
    # Order the results from the most frequently requested to the least frequently 
    # requests.
    priority_values = [ (id, info.priority_modifier) for id, info in six.iteritems(repositories) ]
    priority_values.sort(key=lambda x: x[1], reverse=True)

    # Calculate fingerprints
    this_repository = repositories[priority_values[-1][0]]
    this_configuration = this_repository.configurations[configuration]

    return CommonEnvironmentImports.QuickObject( prioritized_repositories=[ CommonEnvironmentImports.QuickObject( id=id,
                                                                                                                  name=repositories[id].context.name,
                                                                                                                  root=repositories[id].context.root,
                                                                                                                  configuration=repositories[id].context.configuration,
                                                                                                                  is_tool_repository=False,
                                                                                                                )
                                                                            for id, _ in priority_values
                                                                          ],
                                                 version_specs=SourceRepositoryTools.VersionSpecs(tool_version_info, library_version_info),
                                                 fingerprint=this_configuration.Fingerprint,
                                                 calculated_fingerprint=RepositoryInformation.CalculateFingerprint([ this_repository.repository_root, ] + [ dependency.RepositoryRoot for dependency in this_configuration.Dependencies ])
                                               )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _IsImpl(path, valid_items, subdirs=None):
    directories = subdirs or [ item for item in os.listdir(path) if os.path.isdir(os.path.join(path, item)) ]

    for directory in directories:
        if directory not in valid_items:
            return False

    return bool(directories)
