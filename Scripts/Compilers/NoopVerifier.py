# ---------------------------------------------------------------------------
# |  
# |  NoopVerifier.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/20/2015 04:29:14 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
<Used by other scripts>
"""

import os
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

from CommonEnvironment import CommandLine
from CommonEnvironment import Interface

from CommonEnvironment.Compiler import Verifier as VerifierMod
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived
class Verifier( CustomInvocationMixin,
                VerifierMod.Verifier,
              ):
    # ---------------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Noop"
    Description                             = "Verifier that doesn't do anything but can be used when a compiler is required."

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def IsSupported(item):
        return True

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls,
                     invoke_reason,
                     context,
                     status_stream,
                     verbose_stream,
                     verbose,
                   ):
        return 0
    
# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                  output_stream=None,
                                )
def Verify( input,                          # <Redefining build-in type> pylint: disable = W0622
            output_stream=sys.stdout,
            verbose=False,
          ):
    return VerifierMod.CommandLineVerify( Verifier,
                                          input,
                                          output_stream,
                                          verbose,
                                        )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
