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
# |  Copyright David Brownell 2015.
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

from .StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@contextmanager
def CallOnExit(output_stream_or_functor, *functors):
    """
    Invokes the provided functors on exit.
    """

    if hasattr(output_stream_or_functor, "write") and callable(output_stream_or_functor.write):
        output_stream = output_stream_or_functor
    else:
        output_stream = sys.stderr
        functors = [ output_stream_or_functor, ] + list(functors)

    try:
        yield
    finally:
        for functor in functors:
            try:
                functor()
            except:
                output_stream.write(textwrap.dedent(
                    """\
                    ERROR while attempting to unwind stack in CallOnExit.

                        {error}

                    """).format( error=StreamDecorator.LeftJustify(traceback.format_exc(), 4),
                               ))
