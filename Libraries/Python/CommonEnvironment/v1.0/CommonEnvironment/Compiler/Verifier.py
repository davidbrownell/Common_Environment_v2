# ---------------------------------------------------------------------------
# |  
# |  Verifier.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/01/2015 09:13:12 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from CommonEnvironment import Package

Compiler = Package.ImportInit()
 
from .InputProcessingMixin.IndividualInputProcessingMixin import IndividualInputProcessingMixin
from .InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixing
from .OutputMixin.NoOutputMixin import NoOutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <No _Invoke> pylint: disable = E1101
# <Too few public methods> pylint: disable = R0903
class Verifier( IndividualInputProcessingMixin,
                AlwaysInvocationQueryMixing,
                NoOutputMixin,
                Compiler.Base,
              ):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Type = Compiler.Base.TypeValue.File

    IsVerifier = True
    InvokeVerb = "Verifying"

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def Verify( cls,
                context,
                status_stream=sys.stdout,
                verbose_stream=None,
              ):
        return cls._Invoke( context,
                            status_stream=status_stream,
                            verbose_stream=verbose_stream,
                          )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
CommandLineVerify = Compiler.CommandLineInvoke
