# <Invalid module name> pylint: disable = C0103
# ---------------------------------------------------------------------------
# |
# |  SetupEnvironment_custom.py
# |
# |  David Brownell (db@DavidBrownell.com)
# |
# |  09/08/2015 08:10:21 PM
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

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Shell                     # <Unused import> pylint: disable = W0611

# Import SourceRepositoryTools
assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    import SourceRepositoryTools

# REPOSITORY TYPES
# ----------------
# A repository can come in one of two possible types:
#   - Standard
#   - Tool
#
# A 'Standard' repository is a repository that has zero or more dependencies and must
# be activated in its own terminal window. A 'Standard' repository can by dependent upon
# other 'Standard' repositories.
#
# A 'Tool' repository is a repository that provides optional functionality while augmenting
# a 'Standard' repository. A 'Tool' repository must be activated within a terminal window
# that contains an activated 'Standard' repository.
#
# A 'Tool' repository is specified by augmenting the 'Dependencies' method with the 'ToolRepository'
# decorator.

# ---------------------------------------------------------------------------
# @SourceRepositoryTools.ToolRepository
def Dependencies():
    
    # Return a dict in the form:
    #   Key:    Configuration Name
    #   Value:  SourceRepositoryTools.Configuration
    #
    # Note that an explicit dependency upon CommonEnvironment is optional and
    # will be inserted automatically if not provided.
    #
    # Example:
    #       # No explicit configurations
    #       return SourceRepositoryTools.Configuration( [ SourceRepositoryTools.Dependency( "<guid>",
    #                                                                                       "MyCustomRepository",
    #                                                                                       "<optional configuration name>",
    #                                                                                     ),
    #                                                   ],
    #                                                   # Optonal VersionSpecs
    #                                                   SourceRepositoryTools.VersionSpecs( # Optional Tools
    #                                                                                       [ SourceRepositoryTools.VersionInfo("MyCustomTool1", "v1.0"),
    #                                                                                         SourceRepositoryTools.VersionInfo("MyCustomTool2", "v1.5"),
    #                                                                                         ...
    #                                                                                       ],
    #                                                                                       # Optional Libraries
    #                                                                                       { "Python" : [ SourceRepositoryTools.VersionInfo("PythonLibrary1", "v1.0"),
    #                                                                                                      SourceRepositoryTools.VersionInfo("PythonLibrary2", "v8.10"),
    #                                                                                                      ...
    #                                                                                                    ],
    #                                                                                         ...
    #                                                                                       },
    #                                                                                     ),
    #                                                 )
    #
    #       # Explicit configurations
    #       return OrderedDict([ ( "Debug" : SourceRepositoryTools.Configuration(<See above>)) ),
    #                            ( "Release" : SourceRepositoryTools.Configuration(<See above>) ),
    #                          ])

    # Note that it isn't necessary to include "CommonEnvironment" as an explicit dependency,
    # but is shown as an example here.
    return SourceRepositoryTools.Configuration( [ SourceRepositoryTools.Dependency( "CB90253369F54AB5A33F988F31AB6502",
                                                                                    "Common_SimpleSchemaCodeGenerator",
                                                                                  ),
                                                ],
                                              )
           
# ---------------------------------------------------------------------------
def CustomActions():
    return []
