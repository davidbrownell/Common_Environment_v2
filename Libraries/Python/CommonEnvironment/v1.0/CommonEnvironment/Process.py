# ----------------------------------------------------------------------
# |  
# |  Process.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-03-04 17:33:14
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import subprocess
import string
import sys

from six.moves import StringIO

from .CallOnExit import CallOnExit
from .StreamDecorator import StreamDecorator

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
    
    output_stream = StreamDecorator.InitAnsiSequenceStream(output_stream)

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
            newlines_original_output(content)

        # ----------------------------------------------------------------------
        
        output = ConvertNewlines

    if line_delimited_output:
        internal_content = []

        line_delimited_original_output = output
        
        # ----------------------------------------------------------------------
        def OutputFunctor(c):
            if '\n' in c:
                assert c.endswith('\n'), c
                
                line_delimited_original_output("{}{}".format(''.join(internal_content), c))
                internal_content[:] = []

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
    
    args = [ command_line, ]
    kwargs = { "shell" : True,
               "stdout" : subprocess.PIPE,
               "stderr" : subprocess.STDOUT,
               "env" : environment,
             }

    if sys.version_info[0] != 2:
        kwargs["encoding"] = "ansi"

    result = subprocess.Popen(*args, **kwargs)

    with CallOnExit(Flush):
        try:
            # <Invalid variable name> pylint: disable = C0103
            ( CharacterStack_Escape, 
              CharacterStack_LineReset, 
              CharacterStack_Buffered,
            ) = range(3)

            character_stack = []
            character_stack_type = None

            hard_stop = False

            while True:
                if character_stack_type == CharacterStack_Buffered:
                    c = character_stack.pop()

                    assert not character_stack
                    character_stack_type = None

                else:
                    c = result.stdout.read(1)
                    if not c:
                        break

                content = None

                if character_stack_type == CharacterStack_Escape:
                    character_stack.append(c)

                    if c not in string.ascii_letters:
                        continue

                    content = ''.join(character_stack)
                    
                    character_stack = []
                    character_stack_type = None
                
                elif character_stack_type == CharacterStack_LineReset:
                    if c in [ '\r', '\n', ]:
                        character_stack.append(c)
                        continue

                    content = ''.join(character_stack)
                    
                    character_stack = [ c, ]
                    character_stack_type = CharacterStack_Buffered
                
                else:
                    assert character_stack_type == None, character_stack_type

                    value = ord(c)

                    if value == 27: # Esc
                        character_stack.append(c)
                        character_stack_type = CharacterStack_Escape

                        continue

                    if value == 13: # \r
                        character_stack.append(c)
                        character_stack_type = CharacterStack_LineReset

                        continue

                    content = c

                assert content != None

                if output(content) == False:
                    hard_stop = True
                    break
                
            if not hard_stop and character_stack:
                output(''.join(character_stack))

            result = result.wait() or 0

        except IOError:
            result = -1

    if sink == None:
        return result

    return result, sink.getvalue()
