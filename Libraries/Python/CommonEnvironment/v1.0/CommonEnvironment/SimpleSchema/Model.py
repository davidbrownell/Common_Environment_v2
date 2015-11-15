# ---------------------------------------------------------------------------
# |  
# |  Model.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/03/2015 07:24:24 PM
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

from collections import OrderedDict

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaVisitor import SimpleSchemaVisitor
    from SimpleSchemaLexer import SimpleSchemaLexer
    from SimpleSchemaParser import SimpleSchemaParser

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class ParseObserver(Interface):
    
    # ---------------------------------------------------------------------------
    # |  Public Types
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")
    
    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @abstractmethod
    def GetExtensions():
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRequiredMetadata(item_type, name):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetOptionalMetadata(item_type, name):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
@staticderived
class DefaultParserObserver(ParserObserver):

    # ---------------------------------------------------------------------------
    # |  Public Types
    Name                                    = ''

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def GetExtensions():
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetRequiredMetadata():
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetOptionalMetadata():
        return []
    
# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def ParseFiles( source_filenames,
                output_stream,
                optional_observer=None,
              ):
    d = OrderedDict()

    for source_filename in source_filenames:
        d[source_filename] = lambda source_filename=source_filename: open(source_filename).read()

    return ParseEx(d, output_stream, optional_observer)

# ---------------------------------------------------------------------------
def ParseStrings( source_dict,              # { <name> : <string>, }
                  output_stream,
                  optional_observer=None,
                ):
    d = OrderedDict()

    for k, v in source_dict.iteritems():
        d[k] = lambda v=v: v

    return ParseEx(d, output_stream, optional_observer)

# ---------------------------------------------------------------------------
def ParseEx( name_content_generator_dict,
             output_stream,
             optional_observer=None,
           ):
    observer = optional_observer or DefaultParserObserver