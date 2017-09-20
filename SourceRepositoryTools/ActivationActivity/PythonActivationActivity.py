# ---------------------------------------------------------------------------
# |  
# |  PythonActivationActivity.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/23/2015 04:07:52 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
from __future__ import absolute_import 

import os
import sys
import textwrap

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, clsinit
from CommonEnvironment import FileSystem
from CommonEnvironment import Package, ModifiableValue
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import six_plus
from CommonEnvironment import Shell

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from .Impl.ActivationHelpers import ActivateLibraries, \
                                        ActivateLibraryScripts, \
                                        CreateCleanSymLinkStatements

    from .IActivationActivity import IActivationActivity

    __package__ = ni.original

SourceRepositoryTools                       = Package.ImportInit("..")

# ----------------------------------------------------------------------
EASY_INSTALL_PTH_FILENAME                   = "easy-install.pth"
WRAPPERS_FILENAME                           = "__wrappers__.txt"

SCRIPTS_DIR_NAME                            = "__scripts__"
ROOT_DIR_NAME                               = "__root__"

# ----------------------------------------------------------------------
@staticderived
@clsinit
class PythonActivationActivity(IActivationActivity):
    
    # ---------------------------------------------------------------------------
    Name                                    = "Python"
    DelayExecute                            = True
    ProcessLibraries                        = True
    Clean                                   = True

    LibrarySubdirs                          = None      # Initialized in __clsinit__
    ScriptSubdirs                           = None      # Initialized in __clsinit__
    
    BinSubdirs                              = None      # Initialized in __clsinit__
    BinExtension                            = None      # Initialized in __clsinit__
    
    # ---------------------------------------------------------------------------
    @classmethod
    def __clsinit__(cls):
        environment = Shell.GetEnvironment()

        if environment.Name == "Windows":
            cls.LibrarySubdirs = [ "Lib", "site-packages", ]
            cls.ScriptSubdirs = [ "Scripts", ]
            
            cls.BinSubdirs = None
            cls.BinExtension = ".exe"
            
            # ----------------------------------------------------------------------
            def ValidatePythonBinary(bin_name):
                max = 153

                if len(bin_name) >= max:
                    raise Exception(textwrap.dedent(
                        """\
                        The generated Python location binary name is exceedingly long, which will cause problems on Windows.
                        Ensure that this name is less than {} characters by creating a symbolic link to this directory and 
                        then Setup/Activate from that location.

                            {} ({} chars)

                        """).format( max,
                                     bin_name,
                                     len(bin_name),
                                   ))

            # ----------------------------------------------------------------------
            
            cls.ValidatePythonBinary = staticmethod(ValidatePythonBinary)

        elif getattr(environment, "IsLinux", False):
            cls.LibrarySubdirs = [ "lib", "python{python_version_short}", "site-packages", ]
            cls.ScriptSubdirs = [ "Scripts", ]
            
            cls.BinSubdirs = [ "bin", ]
            cls.BinExtension = ''
            
            cls.ValidatePythonBinary = staticmethod(lambda item: None)
            
        else:
            assert False, environment.Name

    # ----------------------------------------------------------------------
    @classmethod
    def GetEnvironmentSettings(cls):
        sub_dict = {}

        for suffix in [ "PYTHON_VERSION",
                        "PYTHON_VERSION_SHORT",
                      ]:
            sub_dict[suffix.lower()] = os.getenv("DEVELOPMENT_ENVIRONMENT_{}".format(suffix))

        generated_dir = os.path.join(os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED"), cls.Name)

        # ----------------------------------------------------------------------
        def Populate(dirs):
            if not dirs:
                return generated_dir

            dirs = [ d.format(**sub_dict) for d in dirs ]
            return os.path.join(generated_dir, *dirs)

        # ----------------------------------------------------------------------

        return QuickObject( library_dir=Populate(cls.LibrarySubdirs),
                            script_dir=Populate(cls.ScriptSubdirs),
                            binary=os.path.join(Populate(cls.BinSubdirs), "python{}".format(cls.BinExtension or '')),
                          )
                                                     
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @classmethod
    def _CreateCommandsImpl( cls,
                             constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
        import SourceRepositoryTools
        del sys.path[0]
        
        dest_dir = os.path.join(generated_dir, cls.Name)
        
        sys.stdout.write("    Cleaning previous content...\n")
        
        if cls.Clean:
            FileSystem.RemoveTree(dest_dir)

        global_actions = [ environment.AugmentPath(dest_dir),
                         ]
        
        # Add the binary environment variable
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

        # Add the script dir environment variable
        script_dir = dest_dir
        if cls.ScriptSubdirs:
            script_dir = os.path.join(script_dir, *cls.ScriptSubdirs)

        global_actions.append(environment.Set( "PYTHON_SCRIPT_DIR",
                                               script_dir,
                                               preserve_original=False,
                                             ))
        
        # Get the python version
        source_dir = os.path.realpath(os.path.join(_script_dir, "..", "..", constants.ToolsDir, cls.Name))
        assert os.path.isdir(source_dir), source_dir
        
        source_dir, python_version = SourceRepositoryTools.GetVersionedDirectoryEx(version_specs.Tools, source_dir)
        assert os.path.isdir(source_dir), source_dir
        assert python_version
        
        # Create a substitution dict that can be used to populate subdirs based on the
        # python version being used.
        if python_version[0] == 'v':
            python_version = python_version[1:]
        
        is_python_version2 = python_version.split('.')[0] == '2'

        sub_dict = { "python_version" : python_version,
                     "python_version_short" : '.'.join(python_version.split('.')[0:2]),
                   }
            
        for k, v in six.iteritems(sub_dict):
            global_actions.append(Shell.AugmentSet("DEVELOPMENT_ENVIRONMENT_{}".format(k.upper()), v))

        # Symbolicly link the reference python files

        # ----------------------------------------------------------------------
        def PythonCallback(libraries, display_sentinel):
            if not cls.ProcessLibraries:
                library_keys = list(six.iterkeys(libraries))

                for library_key in list(six.iterkeys(libraries)):
                    if library_key not in [ "CommonEnvironment", 
                                            "colorama",
                                          ]:
                        del libraries[library_key]

            if is_python_version2:
                global_actions.append(Shell.AugmentSet("PYTHONUNBUFFERED", "1"))

            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)

            # Create the actions
            local_actions = []
            
            if not cls.Clean:
                local_actions += [ environment.Raw(statement) for statement in CreateCleanSymLinkStatements(environment, dest_dir) ]
        
            # Create the dirs that will contain dynamic content
            dynamic_subdirs = {}

            # Prepopulate with the dynamic content
            for subdirs in [ cls.LibrarySubdirs,
                             cls.ScriptSubdirs,
                           ]:
                this_dynamic_subdirs = dynamic_subdirs
        
                for subdir in subdirs:
                    subdir = subdir.format(**sub_dict)
                    this_dynamic_subdirs = this_dynamic_subdirs.setdefault(subdir, {})
        
            # Add a symbolc link for everything found in the source that doesn't
            # already exist in the dest
            easy_install_path_filename = CommonEnvironment.ModifiableValue(None)

            # ----------------------------------------------------------------------
            def TraverseTree(source, dest, dynamic_subdirs):
                if not os.path.isdir(source):
                    return
        
                if not os.path.isdir(dest):
                    os.makedirs(dest)
        
                items = os.listdir(source)
                
                local_actions.append(Shell.Message("{}    Linking {} ({} item{})...".format( display_sentinel,
                                                                                             source, 
                                                                                             len(items), 
                                                                                             's' if len(items) > 1 else '',
                                                                                           )))
                
                for item in items:
                    if item not in dynamic_subdirs:
                        if item == EASY_INSTALL_PTH_FILENAME:
                            assert easy_install_path_filename.value == None
                            easy_install_path_filename.value = os.path.join(source, item)

                            continue

                        local_actions.append(environment.SymbolicLink(os.path.join(dest, item), os.path.join(source, item)))
        
                # We have already created links for everything that isn't dynamic,
                # so we only need to walk what is dynamic.
                for k, v in six.iteritems(dynamic_subdirs):
                    TraverseTree(os.path.join(source, k), os.path.join(dest, k), v)
        
            # ----------------------------------------------------------------------
            
            TraverseTree(source_dir, dest_dir, dynamic_subdirs)
        
            # Apply the libraries
            local_actions.append(Shell.Message("{}    Linking Libraries...".format(display_sentinel)))

            library_dest_dir = os.path.join(dest_dir, *[ subdir.format(**sub_dict) for subdir in cls.LibrarySubdirs ])
        
            for name, info in six.iteritems(libraries):
                for item in os.listdir(info.fullpath):
                    fullpath = os.path.join(info.fullpath, item)
                    if os.path.isdir(fullpath) and item in [ SCRIPTS_DIR_NAME,
                                                             ROOT_DIR_NAME,
                                                           ]:
                        continue
        
                    local_actions.append(environment.SymbolicLink(os.path.join(library_dest_dir, item), fullpath))
                
            script_dest_dir = os.path.join(dest_dir, *cls.ScriptSubdirs)
            
            # Apply the scripts
            local_actions.append(Shell.Message("{}    Linking Scripts...".format(display_sentinel)))
            
            script_actions = ActivateLibraryScripts( script_dest_dir,
                                                     libraries, 
                                                     SCRIPTS_DIR_NAME,
                                                     environment,
                                                   )
            if script_actions:
                for script_action in script_actions:
                    if isinstance(script_action, Shell.Message):
                        script_action.value = "{}        {}".format(display_sentinel, script_action.value)

                    local_actions.append(script_action)

                global_actions.append(environment.AugmentPath(script_dest_dir))
        
                if environment.CategoryName == "Windows":
                    wrappers = []

                    for script_action in script_actions:
                        if isinstance(script_action, Shell.SymbolicLink):
                            name, ext = os.path.splitext(script_action.link_filename)
                            if ext == ".py":
                                source_filename = "{}{}".format( os.path.splitext(script_action.link_source)[0],
                                                                 environment.ScriptExtension,
                                                               )

                                if not os.path.isfile(source_filename):
                                    wrappers.append("{}{}".format(os.path.basename(name), environment.ScriptExtension))

                                    with open("{}{}".format(name, environment.ScriptExtension), 'w') as f:
                                        f.write(textwrap.dedent(
                                            """\
                                            @echo off
                                            python "{}" {}
                                            """).format( script_action.link_filename,
                                                         environment.AllArgumentsScriptVariable,
                                                       ))

                    if wrappers:
                        with open(os.path.join(script_dest_dir, WRAPPERS_FILENAME), 'w') as f:
                            f.write('\n'.join(wrappers))
                
            # Apply the root objects; these are files that need to at the python root. This requirement is extrememly rare.
            local_actions.append(Shell.Message("{}    Linking Roots...".format(display_sentinel)))

            for name, info in six.iteritems(libraries):
                for item in os.listdir(info.fullpath):
                    fullpath = os.path.join(info.fullpath, item)
                    if os.path.isdir(fullpath) and item == ROOT_DIR_NAME:
                        for filename in FileSystem.WalkFiles( fullpath,
                                                              recurse=False,
                                                            ):
                            local_actions.append(Shell.SymbolicLink( os.path.join(bin_dir, os.path.basename(filename)), 
                                                                filename,
                                                              ))

            # Augment easy install
            local_actions += SourceRepositoryTools.DelayExecute( _EasyInstallPathCallback,
                                                                 display_sentinel,
                                                                 easy_install_path_filename.value,
                                                                 library_dest_dir,
                                                               )
                                                                 
            return local_actions
        
        # ----------------------------------------------------------------------
        
        if is_python_version2:
            version_dir = "v2"
        else:
            version_dir = "v3"

        ActivateLibraries( "Python",
                           PythonCallback,
                           environment,
                           repositories,
                           version_specs,
                           generated_dir,
                           library_version_dirs={ ( "v2", "v3" ) : version_dir, },
                         )
        
        return global_actions

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _EasyInstallPathCallback(display_sentinel, original_path_filename, dest_dir):
    eggs = []

    for item in os.listdir(dest_dir):
        if os.path.splitext(item)[1] == ".egg":
            eggs.append(item)

    original_content = '' if not original_path_filename else open(original_path_filename).read()

    dest_filename = os.path.join(dest_dir, EASY_INSTALL_PTH_FILENAME)
    with open(dest_filename, 'w') as f:
        f.write(textwrap.dedent(
            """\
            {}

            {}
            """).format( original_content,
                         '\n'.join([ "./{}".format(egg) for egg in eggs ]),
                       ))

    return [ Shell.Message("{}    Collecting eggs ({} item{})...".format( display_sentinel,
                                                                          len(eggs),
                                                                          '' if len(eggs) == 1 else 's',
                                                                        )),
             Shell.Message(display_sentinel),
           ]

        