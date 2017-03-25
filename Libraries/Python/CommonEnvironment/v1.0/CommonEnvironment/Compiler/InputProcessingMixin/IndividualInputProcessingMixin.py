# ---------------------------------------------------------------------------
# |  
# |  IndividualInputProcessingMixin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/30/2015 05:25:16 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from CommonEnvironment import Package

InputProcessingMixin                        = Package.ImportInit().InputProcessingMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <No __init__> pylint: disable = W0232
# <Too few public methods> pylint: disable = R0903
class IndividualInputProcessingMixin(InputProcessingMixin):

    # ---------------------------------------------------------------------------
    @classmethod
    def _CreateInvocationMetadataItems(cls, inputs, metadata):
        key = cls._GetAttributeName()

        if key in metadata:
            raise Exception("'{}' is a reserved keyword".format(key))

        for input in inputs:
            metadata[key] = input
            yield metadata

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetInputItems(cls, context):
        return [ getattr(context, cls._GetAttributeName()), ]

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetAttributeName(cls):
        if cls.Type == cls.TypeValue.File:
            return "input_filename"
        elif cls.Type == cls.TypeValue.Directory:
            return "input_dir"
        else:
            assert False, (cls.Name, cls.Type)
