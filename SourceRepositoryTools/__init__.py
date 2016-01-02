# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/09/2015 02:27:43 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import textwrap

from collections import OrderedDict
import cPickle as pickle

import semantic_version as sv               # <Unable to import> pylint: disable = F0401
import wrapt 

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

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

# COMMON_ENVIRONMENT_PATH
COMMON_ENVIRONMENT_PATH = os.path.join(DE_FUNDAMENTAL, "Libraries", "Python", "CommonEnvironment", "v1.0")
assert os.path.isdir(COMMON_ENVIRONMENT_PATH), COMMON_ENVIRONMENT_PATH

# Note that this code is potentially called very early during environment initialization,
# meaning we can't rely on custom import functionality and have to manually set the path 
# as a result.

sys.path.insert(0, COMMON_ENVIRONMENT_PATH)
from CommonEnvironment import Shell

# Note that the following libraries aren't used by this module, but those in submodules. Because
# this code is invoked so early in the initialization process, we don't want to sprinkle explicit 
# includes all over the source. Nothing in this package or its subpackages should import from 
# CommonEnironment outside of this code.
import CommonEnvironment

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Package
from CommonEnvironment import RegularExpression
from CommonEnvironment import SourceControlManagement

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

del sys.path[0]

from . import Impl

# The following items are logically part of this global interface, but defined
# within Impl to support better encapsulation.
from .Impl.ActivateEnvironment import LoadOriginalEnvironment
from .Impl.ActivateEnvironment import LoadRepoData

from .Impl import GetRepositoryUniqueId

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
class VersionInfo(object):
    """\
    Mapping of a specific tool or library and version
    """

    def __init__(self, name, version):
        self.Name                           = name
        self.Version                        = version

# ---------------------------------------------------------------------------
class VersionSpecs(object):
    """\
    Collection of tool and/or library version mappings. Note that library
    mappings are organized by language in an attempt to minimize the potential
    for name collisions.
    """

    def __init__( self,
                  tools,                    # [ VersionInfo, ... ]
                  libraries,                # {}, k = language, v = [ VersionInfo, ... ]
                ):
        self.Tools                          = tools
        self.Libraries                      = libraries

# ---------------------------------------------------------------------------
class Dependency(object):
    def __init__( self,
                  id,
                  friendly_name, 
                  configuration=None,
                ):
        self.Id                             = id
        self.FriendlyName                   = friendly_name
        self.Configuration                  = configuration

# ---------------------------------------------------------------------------
class Configuration(object):
    def __init__(self, dependencies=None, version_specs=None):
        self.Dependencies                   = dependencies or []
        self.VersionSpecs                   = version_specs or VersionSpecs([], {})
        
# ---------------------------------------------------------------------------
@wrapt.decorator
def ToolRepository(wrapped, instance, args, kwargs):
    """\
    Signals that a repository is a tool repository (a repository that contains
    items that help in the development process but doesn't contain primitives
    used by other dependent repositories during the build process.
    """
    return wrapped(*args, **kwargs)

# ---------------------------------------------------------------------------
# |
# |  Public Functions
# |
# ---------------------------------------------------------------------------
def SortVersionStrings(version_strings):
    """\
    Sorts the provided strings based on semantic version.
    """

    lookup = {}
    versions = []

    for original_version_string in version_strings:
        version_string = original_version_string

        for potential_prefix in [ "v", "r", ]:
            if version_string.startswith(potential_prefix):
                version_string = version_string[len(potential_prefix):]
                break

        try:
            # Remove leading zeroes from version string values
            parts = []

            for part in version_string.split('.'):
                index = 0

                if len(part) > 1:
                    while index < len(part) and part[index] == '0':
                        index += 1

                parts.append(part[index:])

            version = sv.Version.coerce('.'.join(parts))

            lookup[version] = original_version_string
            versions.append(version)

        except ValueError:
            continue

    versions.sort(reverse=True)

    return [ lookup[v] for v in versions ]

# ---------------------------------------------------------------------------
def GetLatestVersion(version_strings):
    if not version_strings:
        return

    results = SortVersionStrings(version_strings)
    return results[0] if results else None

# ---------------------------------------------------------------------------
def GetVersionedDirectory(version_info, *path_components_or_fullpath):
    """\
    Returns the name of the latest versioned directory.
    """
    return GetVersionedDirectoryEx(version_info, *path_components_or_fullpath)[0]

# ---------------------------------------------------------------------------
def GetVersionedDirectoryEx(version_info, *path_components_or_fullpath):
    """\
    Returns the name of the latest versioned directory and its version.
    """

    # This functionality can be called in 2 different ways:
    #   1) With a fullpath
    #   2) With path components
    if len(path_components_or_fullpath) == 1:
        fullpath = path_components_or_fullpath[0]
        path_components = fullpath.split(os.path.sep)
    else:
        fullpath = os.path.join(*path_components_or_fullpath)
        path_components = path_components_or_fullpath

    # The last part of the path is the name of the library/tool and
    # the second to last part is the type (eg. Tools, Library, etc).
    assert len(path_components) >= 1, fullpath

    name = path_components[-1]

    explicit_version = CommonEnvironment.Get( version_info, 
                                              lambda vi: vi.Name == name,
                                              lambda vi: vi.Version,
                                            )
    if explicit_version != None:
        latest_version = explicit_version
    else:
        latest_version = GetLatestVersion([ item for item in os.listdir(fullpath) if os.path.isdir(os.path.join(fullpath, item)) ])

    if latest_version:
        fullpath = os.path.join(fullpath, latest_version)

    assert os.path.isdir(fullpath), fullpath

    # We could be looking at a directory that contains subfolders
    fullpath = GetCustomizedPath(fullpath)
    assert os.path.isdir(fullpath), fullpath

    return fullpath, latest_version

# ---------------------------------------------------------------------------
def GetCustomizedPathImpl( path, 
                           onError,                     # def Func(path, error_string) -> func result
                           environment=None,
                         ):
    assert os.path.isdir(path), path
    assert onError
    environment = environment or Shell.GetEnvironment()

    while True:
        subdirs = os.listdir(path)

        if Impl.IsOSNameDirectory(path):
            isLinux = getattr(environment, "IsLinux", False)
            
            if environment.Name in subdirs:
                path = os.path.join(path, environment.Name)
            elif isLinux and LINUX_OS_NAME in subdirs:
                path = os.path.join(path, LINUX_OS_NAME)
            elif AGNOSTIC_OS_NAME in subdirs:
                path = os.path.join(path, AGNOSTIC_OS_NAME)
            else:
                return onError(path, "OS names were found in '{}', but no customization was found for '{}' (is {} missing?).".format( path, 
                                                                                                                                      environment.Name, 
                                                                                                                                      ' or '.join([ "'{}'".format(name) for name in ([ LINUX_OS_NAME, ] if isLinux else []) + [ AGNOSTIC_OS_NAME, ] ]),
                                                                                                                                    ))
                
        elif Impl.IsOSVersionDirectory(path, environment):
            if environment.OSVersion in subdirs:
                path = os.path.join(path, environment.OSVersion)
            else:
                return onError(path, "OS versions were found in '{}', but no customization was found for '{}'.".format(path, environment.OSVersion))

        elif Impl.IsOSArchitectureDirectory(path, environment):
            if environment.OSArchitecture in subdirs:
                path = os.path.join(path, environment.OSArchitecture)
            else:
                return onError(path, "OS architectures were found in '{}', but no customization was found for '{}'.".format(path, environment.OSArchitecture))

        else:
            break

    return path

# ---------------------------------------------------------------------------
def GetCustomizedPath(path, environment=None):
    """\
    Drill into environment-specific folders if they exist.
    """

    assert os.path.isdir(path), path
    environment = environment or Shell.GetEnvironment()

    # ---------------------------------------------------------------------------
    def OnCustomizedPathError(path, error):
        raise Exception(error)

    # ---------------------------------------------------------------------------
    
    path = GetCustomizedPathImpl(path, OnCustomizedPathError, environment=environment)    

    # At this point, we are either looking at the actual path of the item or a directory
    # that contains the bits that have been installed to a different location. If there
    # is a pointer file, open it and redirect to the specified location.
    potential_install_location_filename = os.path.join(path, INSTALL_LOCATION_FILENAME)
    if os.path.isfile(potential_install_location_filename):
        path = open(potential_install_location_filename).read().strip()
        if not os.path.isdir(path):
            raise Exception("The install location file at '{}' pointed to '{}', but it does not exist.".format(potential_install_location_filename, path))

    return path

# ---------------------------------------------------------------------------
def DelayExecute(method, *args, **kwargs):
    return DelayExecuteWithPython(os.getenv("PYTHON_BINARY"), method, *args, **kwargs)
    
# ---------------------------------------------------------------------------
def DelayExecuteWithPython(python_binary, method, *args, **kwargs):
    """\
    The vast majority of activation activities can be created at script generation time.
    But, there are some action that must be run at execution time, as they rely on information
    or state changes output by the statements that run immediately before them.

    For example, an action may rely on an environment variable being created; this environment
    variable will not exist at generation time (as the code to create the variable will
    have not been executed yet).

    In situations like this, this method will create a series of Shell commands that
    run the provided method at execution time rather than code generation time.
    """

    assert method

    # Create the statements to invoke the provided method, capture the output, and then 
    # execute it.

    environment = Shell.GetEnvironment()

    script_tempfile = environment.CreateTempFilename(environment.ScriptExtension)
    pickle_tempfile = environment.CreateTempFilename(".pickle")

    # Write the arguments
    with open(pickle_tempfile, 'w') as f:
        f.write(pickle.dumps((args, kwargs)))

    file_path, file_name = os.path.split(method.func_code.co_filename)
    file_name = os.path.splitext(file_name)[0]

    python_code = textwrap.dedent(
        """\
        import os
        import sys
        
        import cPickle as pickle

        sys.path.insert(0, r"{common_environment_path}")
        from CommonEnvironment import Shell
        from CommonEnvironment.StreamDecorator import StreamDecorator
        del sys.path[0]

        sys.path.insert(0, r"{file_path}")
        from {file_name} import {method_name}
        del sys.path[0]

        # Read the arguments
        with open(r"{pickle_tempfile}") as f:
            args, kwargs = pickle.loads(f.read())

        try:
            result = {method_name}(*args, **kwargs)
            
            if result == None:
                rval = 0
                commands = []
            elif isinstance(result, tuple):
                rval, commands = result
            else:
                rval = 0
                commands = result

        except:
            rval = -1
            commands = []

            import traceback
            sys.stderr.write("ERROR: {{}}".format(StreamDecorator.LeftJustify(traceback.format_exc(), len("ERROR: "))))
            
        if rval != 0:
            messages = [ command for command in commands if isinstance(command, Shell.Message) ]
            for message in messages:
                sys.stderr.write(message.value)

            sys.stderr.write("\\n")
            sys.exit(rval)

        # Prep for execution
        environment = Shell.GetEnvironment()

        with open(r"{script_tempfile}", 'w') as f:
            f.write(environment.GenerateCommands(commands))

        environment.MakeFileExecutable(r"{script_tempfile}")

        """.format( common_environment_path=COMMON_ENVIRONMENT_PATH,
                    file_path=file_path,
                    file_name=file_name,
                    method_name=method.__name__,
                    script_tempfile=script_tempfile,
                    pickle_tempfile=pickle_tempfile,
                  ))

    python_tempfile = environment.CreateTempFilename(".py")
    with open(python_tempfile, 'w') as f:
        f.write(python_code)

    return [ Shell.Comment("-- Delay executing '{}' in '{}'".format(method.__name__, method.func_code.co_filename)),
             
             Shell.Execute('{} "{}"'.format(python_binary, python_tempfile)),
             Shell.ExitOnError(),
             Shell.Call(script_tempfile),
             Shell.ExitOnError(),

             Shell.RemoveFile(pickle_tempfile),
             Shell.RemoveFile(python_tempfile),
             Shell.RemoveFile(script_tempfile),

             Shell.Comment("-- End delay execution"),
           ]

# ---------------------------------------------------------------------------
def CreateDependencyMap(code_dir):
    
    # Not that this functionality if very similiar to that found in Impl.TraverseDependencies.
    # The difference between the two is this function will compile a map of all repositories
    # under the code dir, while Impl.TraverseDependencies will only traverse environment
    # data created during setup. Theoretically, it is possible for Impl.TraverseDependencies
    # to be implemented in terms of this function, but that would be too inefficient for 
    # general use.

    assert os.path.isdir(code_dir), code_dir
    
    repositories = OrderedDict()

    # Get the repositories
    for scm, directory in SourceControlManagement.EnumSCMDirectories(code_dir):
        result = GetRepositoryUniqueId( directory,
                                        scm=scm,
                                        throw_on_error=False,
                                      )
        if not result:
            continue

        name, unique_id = result

        assert unique_id not in repositories, (unique_id, directory, repositories[unique_id].root)

        repositories[unique_id] = Impl.RepositoryInformation.Load(directory)
        repositories[unique_id].name = name
        repositories[unique_id].root = directory
        repositories[unique_id].priority_modifier = 0

    # Order by priority

    # ---------------------------------------------------------------------------
    def Walk(unique_id, priority_modifier):
        assert unique_id in repositories, unique_id
        repository_info = repositories[unique_id]

        repository_info.priority_modifier += priority_modifier

        for configuration in repository_info.configurations.values():
            for dependency in configuration.Dependencies:
                Walk( dependency.Id,
                      priority_modifier + 1,
                    )

    # ---------------------------------------------------------------------------
    
    for unique_id in repositories.iterkeys():
        Walk(unique_id, 1)

    priority_values = list(repositories.iteritems())
    priority_values.sort(key=lambda x: x[1].priority_modifier, reverse=True)

    # Convert the repositories into a structure that is valuable for processing
    results = OrderedDict()

    for unique_id, repository_info in priority_values:
        results[unique_id] = QuickObject( unique_id=unique_id,
                                          name=repository_info.name,
                                          root=repository_info.root,
                                          configurations=OrderedDict(),
                                        )

        for configuration_name in repository_info.configurations.iterkeys():
            results[unique_id].configurations[configuration_name] = QuickObject( relies_on_list=[],
                                                                                 relied_upon_by_list=[],
                                                                               )

    # Populate by dependencies
    for unique_id, repository_info in priority_values:
        for configuration_name, configuration_info in repository_info.configurations.iteritems():
            # It is possible that a dependency is included more than once (as will be the case if someone
            # includes Common_Environment as a dependency even though a dependency on Common_Environment is implied).
            # Ensure we are only looking at unique dependencies.
            these_dependencies = []
            dependency_lookup = set()

            for dependency in configuration_info.Dependencies:
                if dependency.Id in dependency_lookup:
                    continue

                these_dependencies.append((dependency, repositories[dependency.Id].priority_modifier))
                dependency_lookup.add(dependency.Id)

            # Ensure that the dependencies are ordered based on priority order
            these_dependencies.sort(key=lambda x: x[0], reverse=True)

            for dependency, priority_modifier in these_dependencies:
                results[unique_id].configurations[configuration_name].relies_on_list.append(QuickObject( configuration=dependency.Configuration,
                                                                                                         dependency=results[dependency.Id],
                                                                                                       ))
                results[dependency.Id].configurations[dependency.Configuration].relied_upon_by_list.append(QuickObject( configuration=configuration_name,
                                                                                                                        dependency=results[unique_id],
                                                                                                                      ))

    # Ensure that we can index by repo path as well as id
    for unique_id in results.keys():
        results[results[unique_id].root] = results[unique_id]

    return results

# ---------------------------------------------------------------------------
def DisplayDependencyMap( dependency_map,
                          output_stream=sys.stdout,
                        ):
    for k, v in dependency_map.iteritems():
        if not os.path.isdir(k):
            continue

        output_stream.write(textwrap.dedent(
            """\
            Directory:                    {dir} ({unique_id})
            configurations:
            {configurations}
            
            """).format( dir=k,
                         unique_id=v.unique_id,
                         configurations=StreamDecorator.LeftJustify( '\n'.join([ textwrap.dedent(
                                                                                    """\
                                                                                    {name}
                                                                                      relies_on_list:
                                                                                    {relies_on_list}
                                                                                      
                                                                                      relied_upon_by_list:
                                                                                    {relied_upon_by_list}
                                                                                    """).format( name=ck,
                                                                                                 relies_on_list='\n'.join([ "      - {} <{}> [{}]".format(item.dependency.name, item.configuration, item.dependency.root) for item in cv.relies_on_list ]) if cv.relies_on_list else "      <None>",
                                                                                                 relied_upon_by_list='\n'.join([ "      - {} <{}> [{}]".format(item.dependency.name, item.configuration, item.dependency.root) for item in cv.relied_upon_by_list ]) if cv.relied_upon_by_list else "      <None>",
                                                                                               )
                                                                                 for ck, cv in v.configurations.iteritems() 
                                                                               ]),
                                                                     2,
                                                                     skip_first_line=False,
                                                                   ),
                       ))
