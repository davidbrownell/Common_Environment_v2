# ----------------------------------------------------------------------
# |  
# |  Utilities.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 13:16:51
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import hashlib
import os
import re
import sys
import textwrap

from collections import OrderedDict

import six
import six.moves.cPickle as pickle

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def GenerateCommands( functor,              # def Func() -> []
                      environment,
                      is_debug,
                    ):
    """Returns (result, generated_commands)"""

    assert functor
    assert environment

    commands = []

    try:
        result = functor()

        if isinstance(result, tuple):
            result, commands = result
        else:
            commands = result
            result = 0

    except Exception as ex:
        if is_debug:
            import traceback

            error = traceback.format_exc()
        else:
            error = str(ex)
            
            if not error.endswith('.'):
                error += '.'

        commands = [ CommonEnvironmentImports.Shell.Message("ERROR: {}".format(CommonEnvironmentImports.StreamDecorator.LeftJustify(error, len("ERROR: ")))),
                     CommonEnvironmentImports.Shell.Exit(pause_on_error=True, return_code=-1),
                   ]

        result = -1

    if is_debug:
        sink = six.moves.StringIO()
        CommonEnvironmentImports.StreamDecorator(sink, line_prefix="Debug: ").write(environment.GenerateCommands(commands))
        sink = sink.getvalue()

        commands = [ CommonEnvironmentImports.Shell.Message("{}\n".format(sink)), ] + commands

    return result, commands

# ----------------------------------------------------------------------
def DelayExecute(method, *args, **kwargs):
    """\
    The vast majority of activation activities can be created at script generation time.
    But, there are some actions that must be run at execution time, as they rely on information
    or state changes output by the statements that run immediately before them.

    For example, an action may rely on an environment variable being created; this environment
    variable will not exist at generation time (as the code to create the variable will
    have not been executed yet).

    In situations like this, this method will create a series of Shell commands that
    run the provided method at execution time rather than code generation time.
    """

    assert method

    environment = CommonEnvironmentImports.Shell.GetEnvironment()

    script_tempfile = environment.CreateTempFilename(environment.ScriptExtension)
    python_tempfile = environment.CreateTempFilename(".py")
    pickle_tempfile = environment.CreateTempFilename(".pickle")
    
    # Write the arguments
    with open(pickle_tempfile, 'wb') as f:
        pickle.dump((args, kwargs), f)

    # Write the python code
    with open(python_tempfile, 'w') as f:
        file_path, file_name = os.path.split(six.get_function_code(method).co_filename)
        file_name = [ os.path.splitext(file_name)[0], ]

        # Import by the fully qualified name
        while os.path.isfile(os.path.join(file_path, "__init__.py")):
            potential_file_path, name_part = os.path.split(file_path)
            
            assert potential_file_path != file_path, file_path
            assert name_part

            file_path = potential_file_path
            file_name.insert(0, name_part)

        file_name = '.'.join(file_name)

        f.write(textwrap.dedent(
            """\
            import os
            import sys
            
            import six
            
            import six.moves.cPickle as pickle
        
            sys.path.insert(0, r"{common_environment_path}")
            from CommonEnvironment import Shell
            from CommonEnvironment.StreamDecorator import StreamDecorator
            del sys.path[0]
            
            sys.path.insert(0, r"{file_path}")
            from {file_name} import {method_name}
            del sys.path[0]
            
            # Read the arguments
            with open(r"{pickle_tempfile}", 'rb') as f:
                args, kwargs = pickle.load(f)
                
            try:
                result = {method_name}(*args, **kwargs)
            
                if isinstance(result, tuple):
                    result, commands = result
                elif result is None:
                    result = 0
                    commands = []
                else:
                    commands = result
                    result = 0
                    
            except:
                result = -1
                commands = []
            
                import traceback
                sys.stderr.write("ERROR: {{}}".format(StreamDecorator.LeftJustify(traceback.format_exc(), len("ERROR: "))))
            
            if result != 0:
                messages = [ command for command in commands if isinstance(command, Shell.Message) ]
                for mesage in messages:
                    sys.stderr.write(message.value)
            
                sys.stderr.write("\\n")
                sys.exit(result)
            
            # Prep for execution
            environment = Shell.GetEnvironment()
            
            with open(r"{script_tempfile}", 'w') as f:
                f.write(environment.GenerateCommands(commands))
            
            environment.MakeFileExecutable(r"{script_tempfile}")
            
            """).format( common_environment_path=os.path.join(CommonEnvironmentImports.fundamental_repo, Constants.LIBRARIES_SUBDIR, "Python", "CommonEnvironment", "v1.0"),
                         file_path=file_path,
                         file_name=file_name,
                         method_name=method.__name__,
                         script_tempfile=script_tempfile,
                         pickle_tempfile=pickle_tempfile,
                       ))

    return [ environment.Comment("-- Delay executing '{}' in '{}'".format(method.__name__, six.get_function_code(method).co_filename)),
             
             environment.Execute('{} "{}"'.format(os.getenv("PYTHON_BINARY"), python_tempfile)),
             environment.ExitOnError(),
             environment.Call(script_tempfile),
             environment.ExitOnError(),

             environment.RemoveFile(python_tempfile),
             environment.RemoveFile(pickle_tempfile),
             environment.RemoveFile(script_tempfile),

             environment.Comment("-- End delay execution"),
           ]

# ----------------------------------------------------------------------
_GetRepositoryUniqueId_regex                = None

def GetRepositoryUniqueId( repo_root,
                           scm=None,
                           throw_on_error=True,
                           find_by_scm=True,
                         ):
    global _GetRepositoryUniqueId_regex

    if _GetRepositoryUniqueId_regex is None:
        _GetRepositoryUniqueId_regex = CommonEnvironmentImports.RegularExpression.TemplateStringToRegex(Constants.REPOSITORY_ID_CONTENT_TEMPLATE)

    filename = os.path.join(repo_root, Constants.REPOSITORY_ID_FILENAME)
    if os.path.isfile(filename):
        match = _GetRepositoryUniqueId_regex.match(open(filename).read())
        if not match:
            raise Exception("The content in '{}' appears to be corrupt".format(filename))

        name = match.group("name")
        unique_id = match.group("guid").upper()

    elif find_by_scm:
        if scm is None:
            scm = CommonEnvironmentImports.SourceControlManagement.GetSCM(repo_root, throw_on_error=False)
            if scm is None:
                if throw_on_error:
                    raise Exception("Id information was not found nor could SCM information be extracted from '{}'".format(repo_root))

                return None

        unique_id = scm.GetUniqueName(repo_root)
        name = unique_id

    else:
        if throw_on_error:
            raise Exception("Unable to find repository information for '{}'".format(repo_root))

        return None

    return name, unique_id

# ----------------------------------------------------------------------
def CalculateFingerprint(repo_dirs, relative_root=None):
    """\
    Returns a value that can be used to determine if any configuration info has
    changed for a repo and its dependencies.
    """

    results = {}

    for repo_dir in repo_dirs:
        md5 = hashlib.md5()

        filename = os.path.join(repo_dir, Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                # Skip the file header, as it has no impact on the file's actual contents
                in_file_header = True

                for line in f:
                    if in_file_header and line.lstrip().startswith(b'#'):
                        continue

                    in_file_header = False
                    md5.update(line)

            if relative_root:
                repo_dir = CommonEnvironmentImports.FileSystem.GetRelativePath(relative_root, repo_dir)

            results[repo_dir] = md5.hexdigest()

    return results

# ----------------------------------------------------------------------
def GetLatestVersion(version_strings):
    if not version_strings:
        return

    # Convert the version strings into semantic version values
    import semantic_version

    lookup = {}
    versions = []

    for version_string in version_strings:
        original_version_string = version_string

        for potential_prefix in [ "v", "r", ]:
            if version_string.startswith(potential_prefix):
                version_string = version_string[len(potential_prefix):]
                break

        try:
            # Remove leading zeros from version string values
            parts = []

            for part in version_string.split('.'):
                index = 0

                if len(part) > 1:
                    while index < len(part) and part[index] == '0':
                        index += 1

                parts.append(part[index:])

            version = semantic_version.Version.coerce('.'.join(parts))

            lookup[version] = original_version_string
            versions.append(version)

        except ValueError:
            continue

    if not versions:
        return None

    versions.sort(reverse=True)
    return lookup[versions[0]]

# ----------------------------------------------------------------------
def GetVersionedDirectory(version_info, *path_components_or_fullpath):
    """\
    Returns the name of the latest versioned directory.
    """
    return GetVersionedDirectoryEx(version_info, *path_components_or_fullpath)[0]

# ----------------------------------------------------------------------
def GetVersionedDirectoryEx(version_info, *path_components_or_fullpath):
    """\
    Returns the name of the latest versioned directory and its version.
    """

    # This method can be called in these ways:
    #   1) With a fullpath
    #   2) With path components

    if len(path_components_or_fullpath) == 1:
        fullpath = path_components_or_fullpath[0]
        path_components = fullpath.split(os.path.sep)
    else:
        fullpath = os.path.join(*path_components_or_fullpath)
        path_components = path_components_or_fullpath

    # The last part of the path is the name of the library/tool.
    # The second to last part is the type (e.g. Tools, Library, etc.)
    assert len(path_components) >= 1, fullpath

    name = path_components[-1]

    explict_version = CommonEnvironmentImports.CommonEnvironment.Get( version_info,
                                                                      lambda vi: vi.Name == name,
                                                                      lambda vi: vi.Version,
                                                                    )
    if explict_version is None:
        explict_version = GetLatestVersion([ item for item in os.listdir(fullpath) if os.path.isdir(os.path.join(fullpath, item)) ])
    
    if explict_version:
        fullpath = os.path.join(fullpath, explict_version)

    assert os.path.isdir(fullpath), fullpath

    fullpath = GetCustomizedPath(fullpath)
    assert os.path.isdir(fullpath), fullpath

    return fullpath, explict_version

# ----------------------------------------------------------------------
def GetCustomizedPath(path, environment=None):
    """\
    Drill into environment-specific folders if they exist.
    """

    assert os.path.isdir(path), path
    environment = environment or CommonEnvironmentImports.Shell.GetEnvironment()

    # ----------------------------------------------------------------------
    def OnCustomizedPathError(path, error):
        raise Exception(error)

    # ----------------------------------------------------------------------

    return GetCustomizedPathEx(path, OnCustomizedPathError, environment=environment)

# ----------------------------------------------------------------------
def GetCustomizedPathEx( path,
                         onError,           # def Func(path, error_string) -> GetCustomizedPathEx result value
                         environment=None,
                       ):
    assert os.path.isdir(path), path
    assert onError
    environment = environment or CommonEnvironmentImports.Shell.GetEnvironment()

    while True:
        subdirs = os.listdir(path)

        if IsOSNameDirectory(path):
            if environment.Name in subdirs:
                path = os.path.join(path, environment.Name)
            elif environment.CategoryName in subdirs:
                path = os.path.join(path, environment.CategoryName)
            elif Constants.AGNOSTIC_OS_NAME in subdirs:
                path = os.path.join(path, Constants.AGNOSTIC_OS_NAME)
            else:
                return onError(path, "OS names were found in '{}', but no customization was found for '{}' (is one of {} missing?).".format( path,
                                                                                                                                             environment.Name,
                                                                                                                                             ', '.join([ "'{}'".format(name) for name in [ environment.Name, environment.CategoryName, Constants.AGNOSTIC_OS_NAME, ] ]),
                                                                                                                                           ))

        elif IsOSVersionDirectory(path, environment):
            if environment.OSVersion in subdirs:
                path = os.path.join(path, environment.OSVersion)
            else:
                return onError(path, "OS versions were found in '{}', but no customization was found for '{}'.".format(path, environment.OSVersion))

        elif IsOSArchitectureDirectory(path, environment):
            if environment.OSArchitecture in subdirs:
                path = os.path.join(path, environment.OSArchitecture)
            else:
                return onError(path, "OS architectures were found in '{}', but no customizations were found for '{}'.".format(path, environment.OSArchitecture))

        else:
            break

    return path

# ----------------------------------------------------------------------
def IsOSNameDirectory(path, subdirs=None):
    potential_os_names = set([ Constants.AGNOSTIC_OS_NAME, "src", ])

    for env in CommonEnvironmentImports.Shell.GetPotentialEnvironments():
        potential_os_names.add(env.Name)
        potential_os_names.add(env.CategoryName)

    return _IsImpl(path, potential_os_names, subdirs=subdirs)

# ----------------------------------------------------------------------
def IsOSVersionDirectory(path, environment, subdirs=None):
    return _IsImpl(path, environment.PotentialOSVersionDirectoryNames, subdirs=subdirs)

# ----------------------------------------------------------------------
def IsOSArchitectureDirectory(path, environment, subdirs=None):
    return _IsImpl(path, environment.PotentialOSArchitectureDirectoryNames, subdirs=subdirs)

# ----------------------------------------------------------------------
def GetActivationDir(environment, repo_root, configuration):
    return os.path.join( repo_root,
                         Constants.GENERATED_DIRECTORY_NAME,
                         environment.CategoryName,
                         configuration or "Default",
                       )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _IsImpl(path, valid_items, subdirs=None):
    subdirs = subdirs or [ item for item in os.listdir(path) if os.path.isdir(os.path.join(path, item)) ]

    for subdir in subdirs:
        if subdir not in valid_items:
            return False

    return bool(subdirs)
