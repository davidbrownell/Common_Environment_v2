# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 11:16:50 AM
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

from CommonEnvironment.Interface import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class StringModule(Interface):
    
    # ---------------------------------------------------------------------------
    # |  Public Properties
    @abstractproperty
    def NoneString(self):
        raise Exception("Abstract Property")
    
    @abstractproperty
    def DefaultDelimiter(self):
        raise Exception("Abstract Property")

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @abstractmethod
    def SplitString(value):
        raise Exception("Abstract Method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def ToString(type_info, item):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetItemRegularExpressionStrings(type_info):
        raise Exception("Abstract Property")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def FromString(type_info, item, regex_match, regex_string_index):
        raise Exception("Abstract method")
