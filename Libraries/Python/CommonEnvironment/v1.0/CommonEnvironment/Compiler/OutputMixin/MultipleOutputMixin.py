# ---------------------------------------------------------------------------
# |  
# |  MultipleOutputMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/31/2015 06:01:57 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from CommonEnvironment import Package
from CommonEnvironment.StreamDecorator import StreamDecorator

OutputMixin                                 = Package.ImportInit().OutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <Too few public methods> pylint: disable = R0903
class MultipleOutputMixin(OutputMixin):

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetRequiredContextNames(cls):
        return [ "output_filenames",
               ] + super(MultipleOutputMixin, cls)._GetRequiredContextNames()

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        for output_filename in getattr(context, "output_filenames", []):
            output_dir = os.path.dirname(output_filename)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

        return super(MultipleOutputMixin, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetOutputFilenames(context):
        return context.output_filenames

    # ---------------------------------------------------------------------------
    @classmethod
    def _CleanImpl(cls, context, status_stream, output_stream):
        input_items = cls._GetInputItems(context)

        for output_filename in context.output_filenames:
            if output_filename in input_items:
                continue

            if os.path.isfile(output_filename):
                status_stream.write("Removing '{}'...".format(output_filename))
                with StreamDecorator(status_stream).DoneManager():
                    os.remove(output_filename)

        return super(MultipleOutputMixin, cls)._CleanImpl(context, status_stream, output_stream)
