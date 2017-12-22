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
    #       return OrderedDict([ ( "Debug", SourceRepositoryTools.Configuration(<See above>)) ),
    #                            ( "Release", SourceRepositoryTools.Configuration(<See above>) ),
    #                          ])

    # Note that it isn't necessary to include "CommonEnvironment" as an explicit dependency,
    # but is shown as an example here.
    return SourceRepositoryTools.Configuration( [ SourceRepositoryTools.Dependency( "F4015FA1A91D46FD8D826F6C4F0A50BF",
                                                                                    "CommonEnvironment",
                                                                                  ),
                                                ],
                                              )
           
# ---------------------------------------------------------------------------
def CustomActions():
    return []

# ----------------------------------------------------------------------
# Define one of the following methods if necessary:
#
#       def Commit(data)                    # No configuration-specific activities
#       def Commit(data, configuration)     # Has configuration-specific activities
#
def Commit(data):
    """SCM commit hook event (fired before committing a change on the local repository)"""

    # Data params are defined in :
    #   <DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL>/SourceRepositoryTools/Impl/Hooks/HooksImplParser.SimpleSchema
    #
    # Return values:
    #   - raise Exception on error

    pass

# ----------------------------------------------------------------------
# Define one of the following methods if necessary:
#
#       def Push(data)                      # No configuration-specific activities
#       def Push(data, configuration)       # Has configuration-specific activities
#
def Push(data):
    """SCM push hook event (fired before pushing changes from a local to a remote repository)"""

    # Data params are defined in :
    #   <DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL>/SourceRepositoryTools/Impl/Hooks/HooksImplParser.SimpleSchema
    #
    # Return values:
    #   - raise Exception on error

    pass

# ----------------------------------------------------------------------
# Define one of the following methods if necessary:
#
#       def Pushed(data)                    # No configuration-specific activities
#       def Pushed(data, configuration)     # Has configuration-specific activities
#
def Pushed(data):
    """SCM pushed hook event (fired before committing pushed changes from a remote repository)"""

    # Data params are defined in :
    #   <DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL>/SourceRepositoryTools/Impl/Hooks/HooksImplParser.SimpleSchema
    #
    # Return values:
    #   - raise Exception on error

    pass
