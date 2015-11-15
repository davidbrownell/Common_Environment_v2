# ---------------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/03/2015 06:39:01 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Builds the SimpleSchema grammar
"""

import os
import shutil
import subprocess
import sys

from CommonEnvironment import Build as BuildImpl
from CommonEnvironment import CommandLine
from CommonEnvironment import Shell

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(output_stream=None)
def Build( output_stream=sys.stdout,
         ):
    input_file = os.path.join(_script_dir, "..", "SimpleSchema.g4")
    assert os.path.isfile(input_file), input_file

    output_dir = os.path.join(_script_dir, "..", "Generated")

    command_line = '{script} Compile Python -o "{output_dir}" -no-listener -visitor "{input_file}"'.format(
                        script=Shell.GetEnvironment().CreateScriptName("ANTLR"),
                        output_dir=output_dir,
                        input_file=input_file,
                    )

    result = subprocess.Popen( command_line,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               shell=True,
                             )

    while True:
        line = result.stdout.readline()
        if not line:
            break

        output_stream.write(line)

    return result.wait() or 0

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(output_stream=None)
def Clean( output_stream=sys.stdout,
         ):
    output_dir = os.path.join(_script_dir, "..", "Generated")
    
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)

    return 0

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(BuildImpl.Main(BuildImpl.Configuration( name="BuildSimpleSchemaGrammar",
                                                         requires_output_dir=False,
                                                         priority=1,
                                                       )))
    except KeyboardInterrupt:
        pass
