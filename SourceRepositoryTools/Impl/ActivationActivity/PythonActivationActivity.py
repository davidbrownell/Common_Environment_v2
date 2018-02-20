# ----------------------------------------------------------------------
# |  
# |  PythonActivationActivity.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-14 19:37:00
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

import six

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl import Utilities

from SourceRepositoryTools.Impl.ActivationActivity import ActivationHelpers
from SourceRepositoryTools.Impl.ActivationActivity import IActivationActivity

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
EASY_INSTALL_PTH_FILENAME                   = "easy-install.pth"

SCRIPTS_DIR_NAME                            = "__scripts__"
ROOT_DIR_NAME                               = "__root__"

WRAPPERS_FILENAME                           = "__wrappers__.txt"

# ----------------------------------------------------------------------
@CommonEnvironmentImports.Interface.staticderived
@CommonEnvironmentImports.Interface.clsinit
class PythonActivationActivity(IActivationActivity.IActivationActivity):
    
    # ----------------------------------------------------------------------
    Name                                    = "Python"
    DelayExecute                            = True

    # Set in __clsinit__
    LibrarySubdirs                          = None
    ScriptSubdirs                           = None

    BinSubdirs                              = None
    BinExtension                            = None

    # Set on the command line
    ProcessLibraries                        = True
    Clean                                   = True

    # ----------------------------------------------------------------------
    @classmethod
    def __clsinit__(cls):
        environment = CommonEnvironmentImports.Shell.GetEnvironment()
        
        if environment.CategoryName == "Windows":
            cls.LibrarySubdirs = [ "Lib", "site-packages", ]
            cls.ScriptSubdirs = [ "Scripts", ]

            cls.BinSubdirs = None
            cls.BinExtension = ".exe"

            # ----------------------------------------------------------------------
            def ValidatePythonBinary(fullpath):
                max = 153

                if len(fullpath) > max:
                    raise Exception(textwrap.dedent(
                        """\
                        The generated Python binary name is exceedingly long, which will cause problems on Windows. 
                        Ensure that this name is less than {} characters by creating a symbolic link to this directory
                        and then Setup and Activate from that location.

                            {} ({} chars)

                        """).format( max,
                                     fullpath,
                                     len(fullpath),
                                   ))

            # ----------------------------------------------------------------------

            cls.ValidatePythonBinary = staticmethod(ValidatePythonBinary)

        elif environment.CategoryName == "Linux":
            cls.LibrarySubdirs = [ "lib", "python{python_version_short}", "site-packages", ]
            cls.ScriptSubdirs = [ "Scripts", ]

            cls.BinSubdirs = [ "bin", ]
            cls.BinExtension = ''

            cls.ValidatePythonBinary = staticmethod(lambda item: None)

        else:
            assert False, environment.CategoryName

    # ----------------------------------------------------------------------
    @classmethod
    def GetEnvironmentSettings(cls):
        sub_dict = {}

        for suffix in [ "PYTHON_VERSION",
                        "PYTHON_VERSION_SHORT",
                      ]:
            sub_dict[suffix.lower()] = os.getenv("DEVELOPMENT_ENVIRONMENT_{}".format(suffix))

        generated_dir = os.path.join(os.getenv(Constants.DE_REPO_GENERATED_NAME), cls.Name)

        # ----------------------------------------------------------------------
        def Populate(dirs):
            if not dirs:
                return generated_dir

            dirs = [ d.format(**sub_dict) for d in dirs ]
            return os.path.join(generated_dir, *dirs)

        # ----------------------------------------------------------------------

        return { "library_dir" : Populate(cls.LibrarySubdirs),
                 "script_dir" : Populate(cls.ScriptSubdirs),
                 "binary" : os.path.join(Populate(cls.BinSubdirs), "python{}".format(cls.BinExtension or '')),
               }

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _CreateCommandsImpl( cls,
                             constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        dest_dir = os.path.join(generated_dir, cls.Name)

        sys.stdout.write("    Cleaning previous content...\n")

        if cls.Clean:
            CommonEnvironmentImports.FileSystem.RemoveTree(dest_dir)

        CommonEnvironmentImports.FileSystem.MakeDirs(dest_dir)

        # Add the python path and binaries
        global_actions = [ environment.AugmentPath(dest_dir),
                         ]

        # Add the binary
        bin_dir = dest_dir
        if cls.BinSubdirs:
            bin_dir = os.path.join(bin_dir, *cls.BinSubdirs)
            global_actions.append(environment.AugmentPath(bin_dir))

        bin_file = os.path.join(bin_dir, "python{}".format(cls.BinExtension))
        cls.ValidatePythonBinary(bin_file)

        global_actions.append(environment.Set( "PYTHON_BINARY",
                                               bin_file,
                                               preserve_original=False,
                                             ))

        # Add the script dir environment var
        script_dir = dest_dir
        if cls.ScriptSubdirs:
            script_dir = os.path.join(script_dir, *cls.ScriptSubdirs)

        global_actions.append(environment.Set( "PYTHON_SCRIPT_DIR", 
                                               script_dir,
                                               preserve_original=False,
                                             ))

        global_actions.append(environment.AugmentSet("PYTHONUNBUFFERED", "1"))

        # Get the python version
        source_dir = os.path.realpath(os.path.join(_script_dir, "..", "..", "..", constants.ToolsDir, cls.Name))
        assert os.path.isdir(source_dir), source_dir

        source_dir, python_version = Utilities.GetVersionedDirectoryEx(version_specs.Tools, source_dir)
        assert os.path.isdir(source_dir), source_dir
        assert python_version

        # Create a substitute dict that can be used to populated subdirs based on the 
        # python version being used
        if python_version.startswith('v'):
            python_version = python_version[1:]

        is_python_v2 = python_version.split('.')[0] == '2'

        sub_dict = { "python_version" : python_version,
                     "python_version_short" : '.'.join(python_version.split('.')[:2]),
                   }

        for k, v in six.iteritems(sub_dict):
            global_actions.append(environment.AugmentSet("DEVELOPMENT_ENVIRONMENT_{}".format(k.upper()), v))

        # Activate the libraries

        # ----------------------------------------------------------------------
        def ActivateCallback(libraries):
            if not cls.ProcessLibraries:
                library_keys = list(six.iterkeys(libraries))

                for library_key in list(six.iterkeys(libraries)):
                    if library_key not in [ "CommonEnvironment",
                                            "colorama",
                                          ]:
                        del libraries[library_key]

            # Create the actions
            local_actions = [ environment.EchoOff(),
                            ]

            if not cls.Clean:
                local_actions += [ environment.Raw(statement) for statement in ActivationHelpers.CreateCleanSymLinkStatements(environment, dest_dir) ]

            # Create the dirs that will be populated with dynamic content
            dynamic_subdirs = {}

            # Pre-populate with the dynamic content
            for subdirs in [ cls.LibrarySubdirs,
                             cls.ScriptSubdirs,
                           ]:
                this_dynamic_subdirs = dynamic_subdirs

                for subdir in subdirs:
                    subdir = subdir.format(**sub_dict)
                    this_dynamic_subdirs = this_dynamic_subdirs.setdefault(subdir, {})

            # Add a symbolic link for everything found in the source that doesn't
            # already exist in the dest
            easy_install_path_filename = CommonEnvironmentImports.CommonEnvironment.ModifiableValue(None)

            # ----------------------------------------------------------------------
            def TraverseTree(source, dest, dynamic_subdirs):
                if not os.path.isdir(source):
                    return

                CommonEnvironmentImports.FileSystem.MakeDirs(dest)

                items = os.listdir(source)

                local_actions.append(environment.Message("    Linking {} ({} item{})".format( source,
                                                                                              len(items),
                                                                                              '' if len(items) == 1 else 's',
                                                                                            )))

                for item in items:
                    if item not in dynamic_subdirs:
                        if item == EASY_INSTALL_PTH_FILENAME:
                            assert easy_install_path_filename.value is None
                            easy_install_path_filename.value = os.path.join(source, item)

                            continue

                        elif item == "__pycache__":
                            continue

                        local_actions.append(environment.SymbolicLink(os.path.join(dest, item), os.path.join(source, item)))

                # We have already created links for everything that isn't dynamic,
                # so we only need to walk what is dynamic.
                for k, v in six.iteritems(dynamic_subdirs):
                    TraverseTree(os.path.join(source, k), os.path.join(dest, k), v)

            # ----------------------------------------------------------------------
                        
            TraverseTree(source_dir, dest_dir, dynamic_subdirs)
            
            # Apply the libraries
            local_actions.append(environment.Message("    Linking Libraries ({} item{})...".format( len(libraries),
                                                                                                    '' if len(libraries) == 1 else 's',
                                                                                                  )))
            library_dest_dir = os.path.join(dest_dir, *[ sd.format(**sub_dict) for sd in cls.LibrarySubdirs ])
            
            for name, info in six.iteritems(libraries):
                for item in os.listdir(info.Fullpath):
                    fullpath = os.path.join(info.Fullpath, item)

                    if os.path.isdir(fullpath) and item in [ SCRIPTS_DIR_NAME,
                                                             ROOT_DIR_NAME,
                                                           ]:
                        continue

                    local_actions.append(environment.SymbolicLink(os.path.join(library_dest_dir, item), fullpath))

            # Apply the scripts
            local_actions.append(environment.Message("    Linking Scripts..."))

            script_dest_dir = os.path.join(dest_dir, *[ d.format(**sub_dict) for d in cls.ScriptSubdirs ])

            script_actions = ActivationHelpers.ActivateLibraryScripts( script_dest_dir,
                                                                       libraries,
                                                                       SCRIPTS_DIR_NAME,
                                                                       environment,
                                                                     )
            
            if script_actions:
                for script_action in script_actions:
                    if isinstance(script_action, environment.Message):
                        script_action.value = "        {}".format(script_action.value)

                    local_actions.append(script_action)

                global_actions.append(environment.AugmentPath(script_dest_dir))

                if environment.CategoryName == "Windows":
                    wrappers = []

                    for script_action in script_actions:
                        if not isinstance(script_action, environment.SymbolicLink):
                            continue

                        name, ext = os.path.splitext(script_action.link_filename)
                        if ext != ".py":
                            continue

                        source_filename = "{}{}".format( os.path.splitext(script_action.link_filename)[0],
                                                         environment.ScriptExtension,
                                                       )

                        if not os.path.isfile(source_filename):
                            wrappers.append("{}{}".format(os.path.basename(name), environment.ScriptExtension))

                            with open("{}{}".format(name, environment.ScriptExtension), 'w') as f:
                                f.write(textwrap.dedent(
                                    """\
                                    @echo off
                                    python "{}" %*
                                    """).format(script_action.link_filename))

                    if wrappers:
                        with open(os.path.join(script_dest_dir, WRAPPERS_FILENAME), 'w') as f:
                            f.write('\n'.join(wrappers))

            # Apply the root objects; these are files that need to live at the python root.
            # This requirement is extremely rare.
            local_actions.append(environment.Message("    Linking Roots..."))

            for name, info in six.iteritems(libraries):
                for item in os.listdir(info.Fullpath):
                    fullpath = os.path.join(info.Fullpath, item)

                    if os.path.isdir(fullpath) and item == ROOT_DIR_NAME:
                        for filename in CommonEnvironmentImports.FileSystem.WalkFiles( fullpath,
                                                                                       recurse=False,
                                                                                     ):
                            local_actions.append(environment.SymbolicLink( os.path.join(bin_dir, os.path.basename(filename)),
                                                                           filename,
                                                                         ))

            # Augment easy install
            local_actions += Utilities.DelayExecute( _EasyInstallPathCallback,
                                                     easy_install_path_filename.value,
                                                     library_dest_dir,
                                                   )
            
            return local_actions

        # ----------------------------------------------------------------------

        if is_python_v2:
            version_dir = "v2"
        else:
            version_dir = "v3"

        ActivationHelpers.ActivateLibraries( cls.Name,
                                             ActivateCallback,
                                             environment,
                                             repositories,
                                             version_specs,
                                             generated_dir,
                                             library_version_dirs={ ( "v2", "v3" ) : version_dir, 
                                                                  },
                                           )
        
        return global_actions

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _EasyInstallPathCallback(easy_install_path_filename, dest_dir):
    eggs = []

    for item in os.listdir(dest_dir):
        if os.path.splitext(item)[1] == ".egg":
            eggs.append(item)

    original_content = '' if not easy_install_path_filename else open(easy_install_path_filename).read()

    dest_filename = os.path.join(dest_dir, EASY_INSTALL_PTH_FILENAME)
    with open(dest_filename, 'w') as f:
        f.write(textwrap.dedent(
            """\
            {}

            {}
            """).format( original_content,
                         '\n'.join([ "./{}".format(egg) for egg in eggs ]),
                       ))

    return [ CommonEnvironmentImports.Shell.Message("    Collecting eggs ({} item{})...\n".format( len(eggs),
                                                                                                   '' if len(eggs) == 1 else 's',
                                                                                                 )),
           ]
