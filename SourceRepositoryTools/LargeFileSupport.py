# ----------------------------------------------------------------------
# |  
# |  LargeFileSupport.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-10-24 07:34:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Some SCMs have limitations on the size of files that they support (for example,
GitHub does not support files > 100Mb). This file provides functionality to
deconstruct and construct large files so that conform to these restrictions.
"""

import os
import sys
import textwrap

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import Process

from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( filename=CommandLine.FilenameTypeInfo(),
                                  output_stream=None,
                                )
def Deconstruct( filename,
                 output_stream=sys.stdout,
              ):
    """\
    Deconstructs a large file into smaller chunks.
    """

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nResult: ",
                                                     done_suffix='\n',
                                                   ) as dm:

        command_line = '7z a -t7z "{output}" -v{size}b "{input}"' \
                            .format( output="{}.7z".format(filename),
                                     size=25 * 1024 * 1024, # 25Mb
                                     input=filename,
                                   )

        dm.result = Process.Execute(command_line, dm.stream)
        
        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( filename=CommandLine.FilenameTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def Construct( filename,
               output_stream=sys.stdout,
               quiet=False,
             ):
    """\
    Constructs a large file from smaller chunks.
    """

    if quiet:
        output_stream = None

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nResults: ",
                                                     done_suffix='\n',
                                                   ) as dm:
        if os.path.isfile(filename):
            dm.result = 0
            return dm.result

        if not filename.endswith(".7z.001"):
            filename = "{}.7z.001".format(filename)

        if not os.path.isfile(filename):
            dm.stream.write("ERROR: '{}' is not a valid filename.\n".format(filename))
            dm.result = -1

            return dm.result

        command_line = '7z x "{input}" "-o{output}"' \
                            .format( input=filename,
                                     output=os.path.dirname(filename),
                                   )

        dm.result = Process.Execute(command_line, dm.stream)

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( filename=CommandLine.FilenameTypeInfo(),
                                  output_stream=None,
                                )
def Instructions( filename,
                  output_stream=sys.stdout,
                ):
    filename = FileSystem.GetRelativePath(os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY"), filename)
    
    output_stream.write(textwrap.dedent(
        """\

        1) Deconstruct the large file:                  
                
                python -m SourceRepositoryTools.{script} Deconstruct "{filename}"

        2) Ignore the large file in your SCM.
        3) Add the deconstructed parts in your SCM.
        4) In "{setup_environment}", add code to reconstruct the large file:

                def CustomActions():
                    actions = []

                    ...

                    actions += [ Shell.Message(r"Restoring '{filename}'..."),
                                 Shell.Set( "PYTHONPATH",
                                            os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"),
                                            preserve_original=False,
                                          ),
                                 Shell.Execute(r'python -m SourceRepositoryTools.{script} Construct "{filename}" /quiet'),
                                 Shell.Set( "PYTHONPATH",
                                            None,
                                            preserve_original=False,
                                          ),
                                 Shell.Message("DONE!\\n\\n"),
                               ]

                    return actions

        """).format( script=os.path.splitext(_script_name)[0],
                     filename=filename,
                     setup_environment=os.path.join( os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY"),
                                                     Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME,
                                                   ),
                   ))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass