# ----------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-10-25 16:35:44
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from CommonEnvironment import Build as BuildMod
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

_OUTPUT_DIR                                 = os.path.join(_script_dir, "..", "GeneratedCode")

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_stream=None,
                                )
def Build( force=False,
           output_stream=sys.stdout,
           verbose=False,
         ):
    environment = Shell.GetEnvironment()

    command_line = '{script} Generate PyJson HooksImplParser "{output_dir}" "/input={input}" /plugin_arg=no_serialization:True /output_data_filename_prefix=HooksImplParser{force}{verbose}' \
                        .format( script=environment.CreateScriptName("SimpleSchemaCodeGenerator"),
                                 output_dir=_OUTPUT_DIR,
                                 input=os.path.join(_script_dir, "..", "HooksImplParser.SimpleSchema"),
                                 force=" /force" if force else '',
                                 verbose=" /verbose" if verbose else '',
                               )

    return Process.Execute(command_line, output_stream)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_stream=None,
                                )
def Clean( output_stream=sys.stdout,
         ):
    if os.path.isdir(_OUTPUT_DIR):
        for filename in FileSystem.WalkFiles( _OUTPUT_DIR,
                                              include_file_base_names=[ lambda name: name.startswith("HooksImplParser"),
                                                                      ],
                                            ):
            os.remove(filename)

    return 0

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(BuildMod.Main(BuildMod.Configuration( "Hooks",
                                                        requires_output_dir=False,
                                                      )))
    except KeyboardInterrupt: pass
