# ----------------------------------------------------------------------
# |  
# |  Process.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-03-04 17:33:14
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import subprocess
import string
import sys

from StringIO import StringIO

from .CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def Execute( command_line,
             optional_output_stream_or_functor,
             convert_newlines=True,
             environment=None,
           ):
    return _ExecuteImpl( command_line,
                         convert_newlines=convert_newlines,
                         environment=environment,
                         optional_output_stream_or_functor=optional_output_stream_or_functor,
                         using_colorama=False,
                       )

# ----------------------------------------------------------------------
def ExecuteWithColorama( command_line,
                         convert_newlines=True,
                         environment=None,
                       ):
    import colorama

    assert not sys.stdout.is_autoreset(), "colorama.init must be called with autoreset=False"

    with CallOnExit(lambda: sys.stdout.write(colorama.Style.RESET_ALL)):
        return _ExecuteImpl( command_line,
                             convert_newlines=convert_newlines,
                             environment=environment,
                             optional_output_stream_or_functor=sys.stdout,
                             using_colorama=True,
                           )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ExecuteImpl( command_line,
                  convert_newlines,
                  environment,
                  optional_output_stream_or_functor,
                  using_colorama,
                ):
    assert command_line
    
    sink = None

    if optional_output_stream_or_functor == None:
        sink = StringIO()

        # ----------------------------------------------------------------------
        def SinkOutputFunctor(content):
            sink.write(content)

        # ----------------------------------------------------------------------
        
        optional_output_stream_or_functor = SinkOutputFunctor

    elif hasattr(optional_output_stream_or_functor, "write"):
        output_stream = optional_output_stream_or_functor

        # ----------------------------------------------------------------------
        def StreamOutputFunctor(content):
            output_stream.write(content)

        # ----------------------------------------------------------------------
        
        optional_output_stream_or_functor = StreamOutputFunctor

    result = subprocess.Popen( command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               env=environment,
                             )

    try:
        escape_sequence = []
        newline_sequence = []

        while True:
            c = output_functor.stdout.read(1)
            if not c:
                break

            # Process special chars
            value = ord(c)
            
            # Escape sequences need to be sent to colorama as an atomic string
            if value == 27:     # ASCII ESC
                assert not escape_sequence
                escape_sequence.append(c)
                continue

            if value == 13:     # ASCII '\r'
                newline_sequence.append(c)
                continue

            # Process sequences
            content = None

            if escape_sequence:
                escape_sequence.append(c)

                if c not in string.ascii_letters:
                    continue

                content = ''.join(escape_sequence)
                escape_sequence = []

                if not using_colorama:
                    continue

            elif newline_sequence:
                newline_sequence.append(c)

                content = ''.join(newline_sequence)
                newline_sequence = []

                if convert_newlines and content == '\r\n':
                    content = '\n'

            else:
                content = c

            assert content
            if optional_output_stream_or_functor(content) == False:
                break

        result = result.wait() or 0

    except IOError:
        result = -1

    if sink == None:
        return result

    return result, sink.getvalue()
