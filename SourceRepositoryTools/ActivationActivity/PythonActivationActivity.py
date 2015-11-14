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
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
from __future__ import absolute_import 

import os
import sys
import textwrap

from CommonEnvironment.Interface import staticderived, clsinit
from CommonEnvironment import Package
from CommonEnvironment import Shell

__package__ = Package.CreateName(__package__, __name__, __file__)           # <Redefining builtin> pylint: disable = W0622

import SourceRepositoryTools
from .SourceActivationActivityImpl import SourceActivationActivityImpl

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@staticderived
@clsinit
class PythonActivationActivity(SourceActivationActivityImpl):
    
    # ---------------------------------------------------------------------------
    Name                                    = "Python"
    DelayExecute                            = False

    LibrarySubdirs                          = None      # Initialized in __clsinit__
    ScriptSubdirs                           = None      # Initialized in __clsinit__
    CopyFiles                               = None      # Initialized in __clsinit__
    BinSubdirs                              = None      # Initialized in __clsinit__
    
    # ---------------------------------------------------------------------------
    @classmethod
    def __clsinit__(cls):
        environment = Shell.GetEnvironment()

        if environment.Name == "Windows":
            cls.LibrarySubdirs = [ "Lib", "site-packages", ]
            cls.ScriptSubdirs = [ "Scripts", ]
            cls.CopyFiles = [ os.path.join("Lib", "site-packages", "easy-install.pth"),
                            ]
            cls.BinSubdirs = None
            
        elif getattr(environment, "IsLinux", False):
            cls.LibrarySubdirs = [ "lib", "python2.7", "site-packages", ] # BugBug
            cls.ScriptSubdirs = None
            cls.CopyFiles = None
            cls.BinSubdirs = os.path.join("bin")
            
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
        # Get the python version
        source_dir = os.path.realpath(os.path.join(_script_dir, "..", "..", constants.ToolsDir, cls.Name))
        assert os.path.isdir(source_dir), source_dir

        source_dir = SourceRepositoryTools.GetVersionedDirectory(version_specs.Tools, source_dir)
        assert os.path.isdir(source_dir), source_dir

        dest_dir = os.path.join(generated_dir, cls.Name)

        mappings = {}
        
        for k, v in [ ( cls.LibrarySubdirs, _MapLibrary ),
                      ( cls.ScriptSubdirs, _MapScripts ),
                    ]:
            if k == None:
                continue
                
            mappings[tuple(k)] = v
            
        commands = super(PythonActivationActivity, cls)._CreateCommandsImpl( source_dir,
                                                                             dest_dir,
                                                                             mappings,
                                                                             constants,
                                                                             environment,
                                                                             configuration,
                                                                             repositories,
                                                                             version_specs,
                                                                             generated_dir,
                                                                           )
                                                                           
        if cls.ScriptSubdirs != None:
            commands.append(environment.AugmentPath([ dest_dir, 
                                                      os.path.join(dest_dir, *cls.ScriptSubdirs),
                                                    ]))

        # Set the PYTHON_BINARY (BugBug: Fix this)
        python_binary = os.getenv("PYTHON_BINARY")
        assert os.path.isfile(python_binary), python_binary

        python_binary = os.path.join(dest_dir, os.path.basename(python_binary))
        commands.append(environment.Set( "PYTHON_BINARY",
                                         python_binary,
                                         preserve_original=False,
                                       ))

        # Add the location to the path
        bin_dir = dest_dir
        if cls.BinSubdirs:
            bin_dir = os.path.join(bin_dir, cls.BinSubdirs)
            
        commands.append(environment.AugmentPath(bin_dir))
        
        return commands

# ---------------------------------------------------------------------------
def _MapLibrary(source, dest, name):
    commands = []

    for item in os.listdir(source):
        fullpath = os.path.join(source, item)

        if os.path.isdir(fullpath) and item == "__scripts__":
            continue

        commands.append(Shell.SymbolicLink(os.path.join(dest, item), fullpath))
    
    return commands

# ---------------------------------------------------------------------------
def _MapScripts(source, dest, _name):
    potential_source_dir = os.path.join(source, "__scripts__")
    if not os.path.isdir(potential_source_dir):
        return

    potential_source_dir = SourceRepositoryTools.GetCustomizedPath(potential_source_dir)
    
    commands = []

    for item in os.listdir(potential_source_dir):
        fullpath = os.path.join(potential_source_dir, item)
        assert os.path.isfile(fullpath), fullpath

        commands.append(Shell.SymbolicLink(os.path.join(dest, item), fullpath))

    return commands
