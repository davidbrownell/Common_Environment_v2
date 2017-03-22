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

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, clsinit
from CommonEnvironment import Package, ModifiableValue
from CommonEnvironment import six_plus
from CommonEnvironment import Shell

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from .Impl import ActivateLibraries, \
                      ActivateLibraryScripts, \
                      CreateCleanSymLinkStatements

    from .IActivationActivity import IActivationActivity

    
    __package__ = ni.original

SourceRepositoryTools                       = Package.ImportInit("..")

# ----------------------------------------------------------------------
EASY_INSTALL_PTH_FILENAME                   = "easy-install.pth"

# ----------------------------------------------------------------------
@staticderived
@clsinit
class PythonActivationActivity(IActivationActivity):
    
    # ---------------------------------------------------------------------------
    Name                                    = "Python"
    DelayExecute                            = True

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

    # ---------------------------------------------------------------------------
    @classmethod
    def OutputModifications(cls, generated_dir, output_stream):
        environment = Shell.GetEnvironment()

        dest_dir = os.path.join(generated_dir, cls.Name)
        assert os.path.isdir(dest_dir), dest_dir

        cols = [ 40, 11, 100, ]
        template = "{name:<%d}  {type:<%d}  {fullpath:<%d}\n" % tuple(cols)

        for name, dirs in [ ( "Libraries", cls.LibrarySubdirs ),
                            ( "Scripts", cls.ScriptSubdirs ),
                          ]:
            if dirs == None:
                continue
                
            output_stream.write(textwrap.dedent(
                """\
                {sep}
                {name}
                {sep}

                {header}{underline}
                """).format( sep='=' * len(name),
                             name=name,
                             header=template.format( name="Name",
                                                     type="Type",
                                                     fullpath="Fullpath",
                                                   ),
                             underline=template.format( name='-' * cols[0],
                                                        type='-' * cols[1],
                                                        fullpath='-' * cols[2],
                                                      ),
                           ))

            this_dest_dir = os.path.join(dest_dir, *dirs)
            assert os.path.isdir(this_dest_dir), this_dest_dir

            for item in os.listdir(this_dest_dir):
                fullpath = os.path.join(this_dest_dir, item)
                if environment.IsSymLink(fullpath):
                    continue

                if os.path.isfile(fullpath) and os.path.splitext(fullpath)[1] in [ ".pyc", ".pyo", ]:
                    continue

                output_stream.write(template.format( name=item,
                                                     type="Directory" if os.path.isdir(fullpath) else "File",
                                                     fullpath=fullpath,
                                                   ))

            output_stream.write('\n')

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
        
        # Symbolicly link the reference python files

        # ----------------------------------------------------------------------
        def PythonCallback(libraries, display_sentinel):
            local_actions = []
        
            # Get the python version
            source_dir = os.path.realpath(os.path.join(_script_dir, "..", "..", constants.ToolsDir, cls.Name))
            assert os.path.isdir(source_dir), source_dir
        
            source_dir, version = SourceRepositoryTools.GetVersionedDirectoryEx(version_specs.Tools, source_dir)
            assert os.path.isdir(source_dir), source_dir
            assert version
        
            # Create a substitution dict that can be used to populate subdirs based on the
            # python version being used.
            if version[0] == 'v':
                version = version[1:]
        
            # Create the dirs that will contain dynamic content
            sub_dict = { "python_version" : version,
                         "python_version_short" : '.'.join(version.split('.')[0:2]),
                       }
        
            # Create the actions
            local_actions.append(Shell.Message("{}    Cleaning previous links...".format(display_sentinel)))
            local_actions += [ environment.Raw(statement) for statement in CreateCleanSymLinkStatements(environment, dest_dir) ]
        
            # Prepopulate with the dynamic content
            dynamic_subdirs = {}
            
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
        
            library_dest_dir = os.path.join(dest_dir, *[ subdir.format(**sub_dict) for subdir in cls.LibrarySubdirs ])
        
            for name, info in six.iteritems(libraries):
                for item in os.listdir(info.fullpath):
                    fullpath = os.path.join(info.fullpath, item)
                    if os.path.isdir(fullpath) and item == "__scripts__":
                        continue
        
                    local_actions.append(environment.SymbolicLink(os.path.join(library_dest_dir, item), fullpath))
                
            script_dest_dir = os.path.join(dest_dir, *cls.ScriptSubdirs)
            
            local_actions.append(Shell.Message("{}    Linking Scripts...".format(display_sentinel)))
            
            script_actions = ActivateLibraryScripts( script_dest_dir,
                                                     libraries, 
                                                     "__scripts__",
                                                     environment,
                                                   )
            if script_actions:
                local_actions += script_actions
                global_actions.append(environment.AugmentPath(script_dest_dir))
        
            local_actions += SourceRepositoryTools.DelayExecute( _EasyInstallPathCallback,
                                                                 display_sentinel,
                                                                 easy_install_path_filename.value,
                                                                 library_dest_dir,
                                                               )
                                                                 
            return local_actions
        
        # ----------------------------------------------------------------------
        
        ActivateLibraries( "Python",
                           PythonCallback,
                           environment,
                           repositories,
                           version_specs,
                           generated_dir,
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

        