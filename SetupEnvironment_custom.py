# <Invalid module name> pylint: disable = C0103
# ---------------------------------------------------------------------------
# |
# |  SetupEnvironment_custom.py
# |
# |  David Brownell (db@DavidBrownell.com)
# |
# |  09/08/2015 08:10:21 PM
# |
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import itertools
import os
import sys
import textwrap

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import Shell                     # <Unused import> pylint: disable = W0611
from CommonEnvironment.StreamDecorator import StreamDecorator

# Import SourceRepositoryTools
assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    import SourceRepositoryTools

# ----------------------------------------------------------------------
def Commit(data):
    # Check for valid descriptions
    if not data.description.strip():
        raise Exception("Descriptions must not be empty")

    # Check for file size
    max_size = 95 * 1024 * 1024 # 95 Mb
    errors = []

    for filename in itertools.chain(data.added, data.modified):
        file_size = os.path.getsize(filename)
        if file_size > max_size:
            errors.append(filename)

    if errors:
        instructions = []
        command_line_template = 'python "{script}" Instructions "{{}}"' \
                                    .format( script=os.path.join(os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"), "SourceRepositoryTools", "LargeFileSupport.py"),
                                           )

        for error in errors:
            instructions.append(textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |  Instructions for "{}"
                # ----------------------------------------------------------------------
                """).format(error))

            _, content = Process.Execute(command_line_template.format(error))

            instructions.append(StreamDecorator.LeftJustify( "{}\n\n".format(content.strip()),
                                                             4,
                                                             skip_first_line=False,
                                                           ))

        raise Exception(textwrap.dedent(
                            """\
                            The following files are more than {} and must be preprocessed before they can be
                            checked in:

                                {}

                                {}
                            """).format( FileSystem.GetSizeDisplay(max_size),
                                         StreamDecorator.LeftJustify('\n'.join(errors), 4),
                                         StreamDecorator.LeftJustify(''.join(instructions), 4),
                                       ))
