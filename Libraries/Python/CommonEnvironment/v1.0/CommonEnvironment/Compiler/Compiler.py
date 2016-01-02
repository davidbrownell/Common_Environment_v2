# ---------------------------------------------------------------------------
# |  
# |  Compiler.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/20/2015 04:36:33 PM
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

from CommonEnvironment import Package

CompilerMod = Package.ImportInit()

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <Too few public methods> pylint: disable = R0903
# <Class has no init method> pylint: disable = W0232
class Compiler(CompilerMod.Base):

    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    IsCompiler                              = True
    InvokeVerb                              = "Compiling"

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def Compile( cls,
                 context,
                 status_stream=sys.stdout,
                 verbose_stream=None,
               ):
        # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
        return cls._Invoke( context,
                            status_stream=status_stream,
                            verbose_stream=verbose_stream,
                          )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
CommandLineCompile = CompilerMod.CommandLineInvoke
CommandLineClean = CompilerMod.CommandLineCleanOutputDir