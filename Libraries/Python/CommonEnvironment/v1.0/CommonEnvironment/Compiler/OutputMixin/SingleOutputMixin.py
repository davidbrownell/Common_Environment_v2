# ---------------------------------------------------------------------------
# |  
# |  SingleOutputMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/31/2015 05:41:04 PM
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

from CommonEnvironment import Package
from CommonEnvironment.StreamDecorator import StreamDecorator

OutputMixin = Package.ImportInit().OutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <Too few public methods> pylint: disable = R0903
class SingleOutputMixin(OutputMixin):

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetRequiredContextItems(cls):
        return [ "output_filename",
               ] + super(SingleOutputMixin, cls)._GetRequiredContextItems()

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        context.output_filename = os.path.realpath(context.output_filename)
        
        output_dir = os.path.dirname(context.output_filename)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        return super(SingleOutputMixin, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetOutputFilenames(context):
        return [ context.output_filename, ]

    # ---------------------------------------------------------------------------
    @classmethod
    def _CleanImpl(cls, context, status_stream, output_stream):
        if context.output_filename not in cls._GetInputItems(context) and os.path.isfile(context.output_filename):
            status_stream.write("Removing '{}'...".format(context.output_filename))
            with StreamDecorator(status_stream).DoneManager():
                os.remove(context.output_filename)
                
        return super(SingleOutputMixin, cls)._CleanImpl(context, status_stream, output_stream)
