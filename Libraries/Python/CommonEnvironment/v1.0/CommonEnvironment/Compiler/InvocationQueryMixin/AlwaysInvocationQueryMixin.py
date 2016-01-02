# ---------------------------------------------------------------------------
# |  
# |  AlwaysInvocationQueryMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/30/2015 05:38:57 PM
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

InvocationQueryMixin = Package.ImportInit().InvocationQueryMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <Too few public methods> pylint: disable = R0903
class AlwaysInvocationQueryMixin(InvocationQueryMixin):

    # ---------------------------------------------------------------------------
    # <Unused argument> pylint: disable = W0613
    @classmethod
    def _GetInvokeReason(cls, context, verbose_stream):
        return cls.InvokeReason.always      # <Has no member> pylint: disable = E1101

    # ---------------------------------------------------------------------------
    @staticmethod
    def _PersistContext(context):
        pass
