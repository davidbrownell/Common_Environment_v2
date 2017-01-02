# ---------------------------------------------------------------------------
# |  
# |  NoOutputMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/31/2015 05:40:03 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from CommonEnvironment import Package

OutputMixin = Package.ImportInit().OutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <Too few public methods> pylint: disable = R0903
class NoOutputMixin(OutputMixin):

    # ---------------------------------------------------------------------------
    # <Unused argument> pylint: disable = W0613
    @staticmethod
    def _GetOutputFilenames(context):
        return []

    # ---------------------------------------------------------------------------
    # <Unused argument> pylint: disable = W0613
    @staticmethod
    def _CleanImpl(context, status_stream, output_stream):
        pass
