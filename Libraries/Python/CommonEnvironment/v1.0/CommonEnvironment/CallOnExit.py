# ---------------------------------------------------------------------------
# |  
# |  CallOnExit.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/20/2015 07:16:53 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import textwrap
import traceback

from contextlib import contextmanager

from StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@contextmanager
def CallOnExit( # Argument may be:
                #   functor     +   def Func()
                #   stream      1   error stream
                #   bool        1   True: call only if successful
                #                   False: call only if exceptional
                #                   Default is call always
                *arguments
              ):
    """
    Invokes the provided functors on exit.
    """

    functors = []
    stream = None
    style = None

    for argument in arguments:
        if isinstance(argument, bool):
            if style != None:
                raise Exception("Only 1 bool arg can be specified")
            style = argument

        elif hasattr(argument, "write") and callable(argument.write):
            if stream != None:
                raise Exception("Only 1 stream arg can be specified")
            stream = argument

        else:
            functors.append(argument)

    if not functors:
        raise Exception("No functors provided")

    stream = stream or sys.stderr
    is_successful = [ True, ]

    # ---------------------------------------------------------------------------
    def Invoke():
        if style == None or style == is_successful[0]:
            for functor in functors:
                try:
                    functor()
                except:
                    stream.write(textwrap.dedent(
                        """\
                        ERROR while attempting to unwind stack in CallOnExit.

                            {error}

                        """).format( error=StreamDecorator.LeftJustify(traceback.format_exc(), 4),
                                   ))

    # ---------------------------------------------------------------------------
    
    try:
        yield
    
    except:
        is_successful[0] = False
        raise

    finally:
        Invoke()
