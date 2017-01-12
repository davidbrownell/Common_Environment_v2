# ----------------------------------------------------------------------
# |  
# |  Build.py
# |      Builds Backup.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-01-10 16:59:34
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

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def Build( output_dir,
           output_stream=sys.stdout,
           verbose=False,
         ):
    command_line = '"{script}" Compile "/input={input}" "/output_dir={output_dir}" /no_bundle /no_optimize{verbose}' \
                        .format( script=Shell.GetEnvironment().CreateScriptName("Py2ExeCompiler"),
                                 input=os.path.join(_script_dir, "Backup.py"),
                                 output_dir=output_dir,
                                 verbose='' if not verbose else " /verbose",
                               )

    return Process.Execute(command_line, output_stream)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def Clean( output_dir,
           output_stream=sys.stdout,
         ):
    if not os.path.isdir(output_dir):
        output_stream.write("'{}' does not exist.\n".format(output_dir))
        return 0

    output_stream.write("Removing '{}'...".format(output_dir))
    with StreamDecorator(output_stream).DoneManager():
        FileSystem.RemoveTree(output_dir)

    return 0

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(BuildMod.Main(BuildMod.Configuration( "Backup",
                                                        required_development_environment="Windows",
                                                      )))
    except KeyboardInterrupt: pass
