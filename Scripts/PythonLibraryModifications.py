# ---------------------------------------------------------------------------
# |  
# |  DisplayPythonLibraryModifications.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/13/2015 07:24:09 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Displays modifications made to the local Python library virtual environment.
"""

import os
import re
import sys
import threading

import inflect

from CommonEnvironment import ModifiableValue
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools.ActivationActivity.PythonActivationActivity import PythonActivationActivity

inflect_engine                              = inflect.engine()

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(output_stream=None)
def Display( output_stream=sys.stdout,
           ):
    generated_dir = os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED")
    assert os.path.isdir(generated_dir), generated_dir

    PythonActivationActivity.OutputModifications(generated_dir, output_stream)

    return 0

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraint( input_dir=CommandLine.DirectoryTypeInfo(),
                                 output_stream=None,
                               )
def PatchExecutables( input_dir,
                      output_stream=sys.stdout,
                    ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nResults: ",
                                                     done_suffix='\n',
                                                   ) as dm:
        dm.stream.write("\n")

        dm.stream.write("Searching for potential binaries..")
        
        filenames = []

        with dm.stream.DoneManager( done_suffix_functor=lambda: "{} found".format(inflect_engine.no("binary", len(filenames))),
                                  ) as this_dm:
            filenames = list(FileSystem.WalkFiles( input_dir, 
                                                   include_file_extensions=[ ".exe", ],
                                                   traverse_exclude_dir_names=[ "Generated", ],
                                                 ))
        
            if not filenames:
                return this_dm.result

        modified = []
        modified_lock = threading.Lock()

        with dm.stream.SingleLineDoneManager( "Processing {}...".format(inflect_engine.no("file", len(filenames))),
                                              done_suffix_functor=lambda: "{} modified".format(inflect_engine.no("binary", len(modified))),
                                            ) as this_dm:
            if sys.version_info[0] == 2:
                shebang_line_regex = re.compile(r"(#!.+pythonw?\.exe)")
            else:
                shebang_line_regex = re.compile(b"(#!.+pythonw?\.exe)")

            # ----------------------------------------------------------------------
            def Invoke(filename, on_status_functor):
                on_status_functor("Processing")

                with open(filename, 'rb') as f:
                    original_content = f.read()

                content = shebang_line_regex.split(original_content, maxsplit=1)
                
                if len(content) != 3:
                    return

                content[1] = b"#!python.exe\r\n"

                final_content = b''.join(content)
                assert final_content != original_content

                with open(filename, 'wb') as f:
                    f.write(final_content)

                with modified_lock:
                    modified.append(filename)
                
            # ----------------------------------------------------------------------

            TaskPool.Transform( filenames,
                                Invoke,
                                this_dm.stream,
                              )

        if modified:
            dm.stream.write("\nThe following binaries have been modified:\n{}\n".format('\n'.join([ "    - {}".format(filename) for filename in modified ])))

        return dm.result

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
