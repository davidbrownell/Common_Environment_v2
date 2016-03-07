# ---------------------------------------------------------------------------
# |  
# |  PythonTestParser.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/20/2015 09:25:14 AM
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
import re
import sys

from CommonEnvironment.TestParser import TestParser as TestParserBase

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class TestParser(TestParserBase):

    # ---------------------------------------------------------------------------
    # |  Public Types
    Name                                    = "Python"
    Description                             = "Parses Python unittest output"

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    def IsSupportedCompiler(cls, compiler):
        # Supports any compiler that supports python - use this file as a test subject
        return compiler.IsSupported(_script_fullpath if os.path.splitext(_script_name)[1] == ".py" else "{}.py".format(os.path.splitext(_script_fullpath)[0]))

    # ---------------------------------------------------------------------------
    @classmethod
    def Parse(cls, test_data):
        if re.search(r"^FAILED", test_data, re.DOTALL | re.MULTILINE): 
            return -1

        if re.search(r"^OK\s*$", test_data, re.DOTALL | re.MULTILINE):
            return 0

        return 1

    # ---------------------------------------------------------------------------
    @classmethod
    def CreateInvokeCommandLine(cls, context, debug_on_error):
        command_line = super(TestParser, cls).CreateInvokeCommandLine(context, debug_on_error)
        return 'python "{}"'.format(command_line)
