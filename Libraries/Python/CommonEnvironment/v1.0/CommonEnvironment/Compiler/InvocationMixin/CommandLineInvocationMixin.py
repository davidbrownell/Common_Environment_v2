# ---------------------------------------------------------------------------
# |  
# |  CommandLineInvocationMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/30/2015 05:02:00 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import codecs
import os
import subprocess
import sys
import textwrap

from CommonEnvironment.Interface import abstractmethod
from CommonEnvironment import Shell

from CommonEnvironment.Compiler.InvocationMixin import InvocationMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <Too few public methods> pylint: disable = R0903
class CommandLineInvocationMixin(InvocationMixin):

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def CreateInvokeCommandLine(context, output_stream):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls,
                     invoke_reason,
                     context,
                     status_stream,
                     output_stream,
                   ):
        command_line = cls.CreateInvokeCommandLine(context, output_stream)
        
        result = subprocess.Popen( command_line,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                 )

        while True:
            line = result.stdout.readline()
            if not line:
                break

            output_stream.write(line)

        return result.wait() or 0

    # ---------------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def QuoteArguments( command_line_groups,
                        environment=None,
                      ):
        assert command_line_groups

        environment = environment or Shell.GetEnvironment()
        is_windows = environment.Name == "Windows"

        new_command_line_groups = []

        for clg in command_line_groups:
            new_command_line_groups.append([ clg[0], ])

            for cla in clg[1:]:
                if is_windows and cla.endswith(os.path.sep):
                    cla += os.path.sep

                new_command_line_groups[-1].append('"{}"'.format(cla))

        return new_command_line_groups

    # ---------------------------------------------------------------------------
    @staticmethod
    def PrintCommandLine( command_line_groups,
                          output_stream=None,
                        ):
        assert command_line_groups
        output_stream = output_stream or sys.stdout

        output = []

        if isinstance(command_line_groups, str):
            output.append(command_line_groups)
        else:
            for clg in command_line_groups:
                output.append("{program}\n{args}\n".format( program=clg[0],
                                                            args='\n'.join([ "    {}".format(arg[1:-1]) for arg in clg[1:] ]),
                                                          ))

        output_stream.write(textwrap.dedent(
            """\
            ****************************************
            {}
            ****************************************
            """).format('\n'.join(output)))

    # ---------------------------------------------------------------------------
    @staticmethod
    def CreateResponseFile( filename,
                            command_line_items,
                            requires_utf16,
                          ):
        assert filename
        assert command_line_items

        if requires_utf16:
            def Open(): return codecs.open(filename, 'w', encoding="utf-16")
        else:
            def Open(): return open(filename, 'w')

        with Open() as f:
            f.write(' '.join([ cli.replace('\\', '\\\\') for cli in command_line_items[1:] ]))

        return [ command_line_items[0], "@{}".format(filename), ]
