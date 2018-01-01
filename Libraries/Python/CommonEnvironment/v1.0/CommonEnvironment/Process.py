# ----------------------------------------------------------------------
# |  
# |  Process.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-03-04 17:33:14
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import subprocess
import string
import sys

import six
from six.moves import StringIO

from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def Execute( command_line,
             optional_output_stream_or_functor=None,
             convert_newlines=True,
             line_delimited_output=False,
             environment=None,
           ):
    return _ExecuteImpl( command_line,
                         convert_newlines=convert_newlines,
                         environment=environment,
                         optional_output_stream_or_functor=optional_output_stream_or_functor,
                         line_delimited_output=line_delimited_output,
                       )

# ----------------------------------------------------------------------
def ExecuteWithColorama( command_line,
                         convert_newlines=True,
                         line_delimited_output=False,
                         environment=None,
                         output_stream=sys.stdout,
                       ):
    import colorama
    
    with CallOnExit(lambda: output_stream.write(colorama.Style.RESET_ALL)):
        result = _ExecuteImpl( command_line,
                               convert_newlines=convert_newlines,
                               environment=environment,
                               optional_output_stream_or_functor=output_stream,
                               line_delimited_output=line_delimited_output,
                             )

    return result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ExecuteImpl( command_line,
                  convert_newlines,
                  environment,
                  optional_output_stream_or_functor,
                  line_delimited_output,
                ):
    assert command_line

    # <Invalid variable name> pylint: disable = C0103
    
    sink = None
    output = None

    if optional_output_stream_or_functor == None:
        sink = StringIO()

        # ----------------------------------------------------------------------
        def SinkOutputFunctor(content):
            sink.write(content)

        # ----------------------------------------------------------------------
        
        output = SinkOutputFunctor

    elif hasattr(optional_output_stream_or_functor, "write"):
        output_stream = optional_output_stream_or_functor

        # ----------------------------------------------------------------------
        def StreamOutputFunctor(content):
            output_stream.write(content)

        # ----------------------------------------------------------------------
        
        output = StreamOutputFunctor
        
    else:
        output = optional_output_stream_or_functor

    if convert_newlines:

        newlines_original_output = output

        # ----------------------------------------------------------------------
        def ConvertNewlines(content):
            content = content.replace('\r\n', '\n')
            return newlines_original_output(content)

        # ----------------------------------------------------------------------
        
        output = ConvertNewlines

    if line_delimited_output:
        internal_content = []

        line_delimited_original_output = output
        
        # ----------------------------------------------------------------------
        def OutputFunctor(c):
            if '\n' in c:
                assert c.endswith('\n'), c
                
                content = "{}{}".format(''.join(internal_content), c)
                internal_content[:] = []

                return line_delimited_original_output(content)

            else:
                internal_content.append(c)

        # ----------------------------------------------------------------------
        def Flush():
            if internal_content:
                line_delimited_original_output(''.join(internal_content))
                internal_content[:] = []

        # ----------------------------------------------------------------------
        
        output = OutputFunctor

    else:
        # ----------------------------------------------------------------------
        def Flush():
            pass

        # ----------------------------------------------------------------------
    
    if environment and sys.version_info[0] == 2:
        # Keys and values must be strings, which can be a problem if the environment was extracted from unicode data
        import unicodedata
        
        # ----------------------------------------------------------------------
        def ConvertToString(item):
            return unicodedata.normalize('NFKD', item ).encode('ascii','ignore')
            
        # ----------------------------------------------------------------------
        
        keys = list(six.iterkeys(environment))
        
        for key in keys:
            value = environment[key]
            
            if isinstance(key, unicode):
                del environment[key]
                key = ConvertToString(key)
                
            if isinstance(value, unicode):
                value = ConvertToString(value)

            environment[key] = value

    args = [ command_line, ]

    kwargs = { "shell" : True,
               "stdout" : subprocess.PIPE,
               "stderr" : subprocess.STDOUT,
               "env" : environment,
             }

    result = subprocess.Popen(*args, **kwargs)

    ( CharacterStack_Escape, 
      CharacterStack_LineReset, 
      CharacterStack_Buffered,
    ) = range(3)
        
    # Handle differences between bytes and strings in Python 3
    if sys.version_info[0] == 2:
        CharToValue = lambda c: c
        IsAsciiLetter = lambda c: c in string.ascii_letters
        IsNewLine = lambda c: c in [ '\r', '\n', ]
        IsEsc = lambda c: c == '\033'
        ToAsciiString = lambda c: ''.join(c)
    else:
        # ----------------------------------------------------------------------
        def CharToValue(c):
            return ord(c)

        # ----------------------------------------------------------------------
        def IsAsciiLetter(c):
            if c >= ord('a') and c <= ord('z'):
                return True

            if c >= ord('A') and c <= ord('Z'):
                return True

            return False

        # ----------------------------------------------------------------------
        def IsNewLine(c):
            return c in [ 10, 13, ]         # '\r', '\n'

        # ----------------------------------------------------------------------
        def IsEsc(c):
            return c == 27                  # '\033'

        # ----------------------------------------------------------------------
        def ToAsciiString(c):
            result = bytearray(c)
            
            for codec in [ "utf-8", 
                           "ansi", 
                         ]:
                try:
                    return result.decode(codec)
                except UnicodeDecodeError:
                    pass
                    
            raise UnicodeDecodeError()

        # ----------------------------------------------------------------------

    with CallOnExit(Flush):
        try:
            character_stack = []
            character_stack_type = None

            hard_stop = False

            while True:
                if character_stack_type == CharacterStack_Buffered:
                    value = character_stack.pop()

                    assert not character_stack
                    character_stack_type = None

                else:
                    c = result.stdout.read(1)
                    if not c:
                        break

                    value = CharToValue(c)

                content = None

                if character_stack_type == CharacterStack_Escape:
                    character_stack.append(value)

                    if not IsAsciiLetter(value):
                        continue

                    content = character_stack

                    character_stack = []
                    character_stack_type = None

                elif character_stack_type == CharacterStack_LineReset:
                    if IsNewLine(value):
                        character_stack.append(value)
                        continue

                    content = character_stack

                    character_stack = [ value, ]
                    character_stack_type = CharacterStack_Buffered

                else:
                    assert character_stack_type == None, character_stack_type

                    if IsEsc(value):
                        character_stack.append(value)
                        character_stack_type = CharacterStack_Escape

                        continue

                    elif IsNewLine(value):
                        character_stack.append(value)
                        character_stack_type = CharacterStack_LineReset

                        continue

                    content = [ value, ]

                assert content

                if output(ToAsciiString(content)) == False:
                    hard_stop = True
                    break
            
            if not hard_stop and character_stack:
                output(ToAsciiString(character_stack))

            result = result.wait() or 0

        except IOError:
            result = -1

    if sink == None:
        return result

    return result, sink.getvalue()
