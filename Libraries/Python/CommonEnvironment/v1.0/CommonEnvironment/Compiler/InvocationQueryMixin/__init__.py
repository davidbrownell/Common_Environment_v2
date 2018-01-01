# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/30/2015 05:37:05 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from CommonEnvironment import Enum
from CommonEnvironment.Interface import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class InvocationQueryMixin(Interface):

    # <Wrong indentation> pylint: disable = C0330
    InvokeReason                            = Enum.Create( "always",
                                                           "force",
                                                           "prev_context_missing",
                                                           "newer_generators",
                                                           "missing_output",
                                                           "removed_output",
                                                           "newer_input",
                                                           "different_metadata",
                                                           "opt_in",
                                                          )

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetInvokeReason(context, verbose_stream):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _PersistContext(context):
        raise Exception("Abstract method")
