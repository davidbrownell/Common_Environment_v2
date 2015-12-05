# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/20/2015 09:40:13 AM
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

from CommonEnvironment.Interface import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# <Too many instance attributes> pylint: disable = R0902
# <Too few public methods> pylint: disable = R0903
class Results(object):
    
    # ---------------------------------------------------------------------------
    def __init__( self,
                  
                  test_result=None,
                  test_output=None,
                  test_duration=None,

                  coverage_result=None,
                  coverage_output=None,
                  coverage_duration=None,

                  data=None,
                  total_percentage=None,
                  individual_percentages=None,  # { "<name>" : %, }
                ):
        self.test_result                    = test_result
        self.test_output                    = test_output
        self.test_duration                  = test_duration

        self.coverage_result                = coverage_result
        self.coverage_output                = coverage_output
        self.coverage_duration              = coverage_duration

        self.data                           = data
        self.total_percentage               = total_percentage
        self.individual_percentages         = individual_percentages

# ---------------------------------------------------------------------------
class CodeCoverageExtractor(Interface):

    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        raise Exception("Abstract property")

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def ValidateEnvironment():
        """Return an error message if the module cannot run in the current environment"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsSupportedCompiler(compiler):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Execute( compiler,
                 context,
                 command_line,
                 includes=None,
                 excludes=None,
                 verbose=False,
               ):
        """Returns (<return code>, <output>)"""
        raise Exception("Abstract method")
