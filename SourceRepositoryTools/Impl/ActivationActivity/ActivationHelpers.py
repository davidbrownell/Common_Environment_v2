# ----------------------------------------------------------------------
# |  
# |  ActivationHelpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-15 08:47:01
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

from collections import OrderedDict

import six
from six.moves import cPickle as pickle

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl import Utilities

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class LibraryInfo(object):
    
    # ----------------------------------------------------------------------
    def __init__(self, repository, version_string, fullpath):
        self.Repo                       = repository
        self.Version                    = version_string
        self.Fullpath                   = fullpath

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjStrImpl(self)

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def ActivateLibraries( name,
                       create_commands_func,            # def Func(libraries) -> environment commands
                       environment,
                       repositories,
                       version_specs,
                       generated_dir,
                       library_version_dirs=None,       # { ( <potential_version_dir>, ) : <dir_to_use>, }
                     ):
    library_version_dirs = library_version_dirs or {}

    version_info = version_specs.Libraries.get(name, [])
    
    # Create the libraries
    libraries = OrderedDict()

    errors = []

    for repository in repositories:
        potential_library_dir = os.path.join(repository.Root, Constants.LIBRARIES_SUBDIR, name)
        if not os.path.isdir(potential_library_dir):
            continue

        for item in os.listdir(potential_library_dir):
            if item in libraries:
                errors.append(textwrap.dedent(
                    """\
                    The library '{name}' has already been defined.

                        New:                {new_name}{new_config} <{new_id}> [{new_root}]
                        Original:           {original_name}{original_config} <<{original_version}>> <{original_id}> [{original_root}]

                    """).format( name=item,
                                 new_name=repository.Name,
                                 new_config=" ({})".format(repository.Configuration) if repository.Configuration else '',
                                 new_id=repository.Id,
                                 new_root=repository.Root,
                                 original_name=libraries[name].Repo.Name,
                                 original_config=" ({})".format(libraries[name].Repo.Configuration) if libraries[name].Repo.Configuration else '',
                                 original_version=libraries[name].Version.Version,
                                 original_id=libraries[name].Reop.Id,
                                 original_root=libraries[name].Repo.Root,
                               ))

                continue

            fullpath = os.path.join(potential_library_dir, item)

            # Drill into the fullpath
            version = CommonEnvironmentImports.CommonEnvironment.ModifiableValue(None)

            # ----------------------------------------------------------------------
            def GetVersionedDirectoryEx(fullpath):
                fullpath, version.value = Utilities.GetVersionedDirectoryEx(version_info, fullpath)
                return fullpath

            # ----------------------------------------------------------------------
            def AugmentLibraryDir(fullpath):
                while True:
                    prev_fullpath = fullpath

                    dirs = [ item for item in os.listdir(fullpath) if os.path.isdir(os.path.join(fullpath, item)) ]

                    for library_versions, this_version in six.iteritems(library_version_dirs):
                        applies = True

                        for directory in dirs:
                            if directory not in library_versions:
                                applies = False
                                break

                        if not applies:
                            continue

                        if this_version not in dirs:
                            return None

                        fullpath = os.path.join(fullpath, this_version)
                        break

                    if prev_fullpath == fullpath:
                        break

                return fullpath

            # ----------------------------------------------------------------------

            try:
                should_apply = True

                for index, method in enumerate([ Utilities.GetCustomizedPath,
                                                 AugmentLibraryDir,
                                                 GetVersionedDirectoryEx,
                                                 Utilities.GetCustomizedPath,
                                                 AugmentLibraryDir,
                                               ]):
                    result = method(fullpath)
                    if result is None:
                        should_apply = False
                        break

                    fullpath = result
                    assert os.path.isdir(fullpath), (index, fullpath)

                if should_apply:
                    libraries[item] = LibraryInfo(repository, version.value, fullpath)

            except Exception as ex:
                sys.stdout.write("    WARNING: {}\n".format(ex))

    if errors:
        raise Exception(''.join(errors))

    commands = create_commands_func(libraries)

    environment.ExecuteCommands(commands, sys.stdout)

    WriteLibraryInfo( generated_dir,
                      name,
                      libraries,
                    )

# ----------------------------------------------------------------------
def ActivateLibraryScripts( dest_dir,
                            libraries,
                            library_script_dir_name,
                            environment,
                          ):
    """\
    Walks all libraries looking for a subdir named <library_script_dir_name>. When
    found, will walk all items in that dir and map the files, ensuring naming conflicts
    are avoided.
    """

    # ----------------------------------------------------------------------
    ScriptInfo                              = CommonEnvironmentImports.NamedTuple( "ScriptInfo",
                                                                                   "Fullpath",
                                                                                   "Repo",
                                                                                 )

    # ----------------------------------------------------------------------

    actions = []

    all_scripts = OrderedDict()

    for info in six.itervalues(libraries):
        potential_dir = os.path.join(info.Fullpath, library_script_dir_name)
        if not os.path.isdir(potential_dir):
            continue

        try:
            potential_dir = Utilities.GetCustomizedPath(potential_dir)
        except Exception as ex:
            actions.append(environment.Message("WARNING: {}\n".format(str(ex))))
            continue

        for item in os.listdir(potential_dir):
            item_name = item

            if item in all_scripts:
                # ----------------------------------------------------------------------
                def GenerateNewName(repository):
                    filename, ext = os.path.splitext(item)

                    new_name = "{}.{}{}".format( filename,
                                                 repository.Name,
                                                 ext,
                                               )

                    actions.append(environment.Message("To avoid naming conflicts, the script '{}' has been renamed to '{}' ({} <{}> [{}]).\n" \
                                                            .format( item,
                                                                     new_name,
                                                                     repository.Name,
                                                                     repository.Id,
                                                                     repository.Root,
                                                                   )))

                    return new_name

                # ----------------------------------------------------------------------

                if all_scripts[item] is not None:
                    new_name = GenerateNewName(all_scripts[item].Repo)

                    all_scripts[new_name] = all_scripts[item]

                    # Keep this item in the list to show that future conflicts need
                    # to be renamed, but no replacement names are necessary.
                    all_scripts[item] = None

                item_name = GenerateNewName(info.Repository)

            all_scripts[item_name] = ScriptInfo( os.path.join(potential_dir, item),
                                                 info.Repo,
                                               )

    CommonEnvironmentImports.FileSystem.RemoveTree(dest_dir)
    os.makedirs(dest_dir)

    if all_scripts:
        for script_name, script_info in six.iteritems(all_scripts):
            if script_info is None:
                continue

            actions.append(environment.SymbolicLink(os.path.join(dest_dir, script_name), script_info.Fullpath))

    return actions

# ----------------------------------------------------------------------
def ActivateLibraryComponents( dest_dir,
                               libraries,
                               library_component_dir_name,
                               environment,
                             ):
    """\
    Walks all libraries, looking for subdirs named <library_component_dir_name>. When
    found, will map those dirs to the specified dir name.
    """

    actions = []

    for name, info in six.iteritems(libraries):
        potential_dir = os.path.join(info.Fullpath, library_component_dir_name)
        if not os.path.isdir(potential_dir):
            continue

        actions.append(environment.SymbolicLink( os.path.join(dest_dir, name),
                                                 potential_dir,
                                               ))

    CommonEnvironmentImports.FileSystem.RemoveTree(dest_dir)
    os.makedirs(dest_dir)

    return actions

# ----------------------------------------------------------------------
def CreateCleanSymLinkStatements(environment, path):
    if not os.path.isdir(path):
        return []

    statements = []

    for root, dirs, filenames in os.walk(path):
        new_traverse_dirs = []

        for directory in dirs:
            fullpath = os.path.join(root, directory)

            if environment.IsSymLink(fullpath):
                statement = environment.DeleteSymLink(fullpath, command_only=True)
                if statement:
                    statements.append(statement)

            else:
                new_traverse_dirs.append(directory)

        dirs[:] = new_traverse_dirs

        for filename in filenames:
            fullpath = os.path.join(root, filename)

            if environment.IsSymLink(fullpath):
                statement = environment.DeleteSymLink(fullpath, command_only=True)
                if statement:
                    statements.append(statement)

    return statements

# ----------------------------------------------------------------------
def WriteLibraryInfo(generated_dir, name, libraries):
    with open(os.path.join(generated_dir, "{}.txt".format(name)), 'w') as f:
        library_keys = list(six.iterkeys(libraries))
        library_keys.sort(key=str.lower)

        col_sizes = [ 40, 15, 60, ]

        template = "{{name:<{0}}}  {{version:<{1}}}  {{fullpath:<{2}}}".format(*col_sizes)

        f.write(textwrap.dedent(
            """\
            {}
            {}
            {}
            """).format( template.format( name="Name",
                                          version="Version",
                                          fullpath="Fullpath",
                                        ),
                         template.format(**{ k : v for k, v in six.moves.zip( [ "name", "version", "fullpath", ],
                                                                              [ '-' * col_size for col_size in col_sizes ],
                                                                            ) }),
                         '\n'.join([ template.format( name=k,
                                                      version=libraries[k].Version,
                                                      fullpath=libraries[k].Fullpath,
                                                    )
                                     for k in sorted(six.iterkeys(libraries), key=str.lower)
                                   ]),
                       ))

    with open(os.path.join(generated_dir, "{}.pickle".format(name)), 'wb') as f:
        pickle.dump(libraries, f)
