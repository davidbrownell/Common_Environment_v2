# ----------------------------------------------------------------------
# |  
# |  Configuration.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 14:08:54
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from SourceRepositoryTools.Impl import CommonEnvironmentImports

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class VersionInfo(object):
    """\
    Mapping of a specific tool or library and version
    """

    # ----------------------------------------------------------------------
    def __init__(self, name, version):
        self.Name                           = name
        self.Version                        = version

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjStrImpl(self)

# ----------------------------------------------------------------------
class VersionSpecs(object):
    """\
    Collection of tool and/or library version mappings. Note that library
    mappings are organized by language in an attempt to minimize the potential
    for name collisions.
    """

    # ----------------------------------------------------------------------
    def __init__( self,
                  tools,                    # [ VersionInfo, ... ]
                  libraries,                # {}, k = language, v = [ VersionInfo, ... ]
                ):
        self.Tools                          = tools
        self.Libraries                      = libraries

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjStrImpl(self)

# ---------------------------------------------------------------------------
class Dependency(object):
    
    # ----------------------------------------------------------------------
    def __init__( self,
                  id,
                  friendly_name, 
                  configuration=None,
                ):
        self.Id                             = id
        self.FriendlyName                   = friendly_name
        self.Configuration                  = configuration
        # self.RepositoryRoot is added during SetupEnvironment

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjStrImpl(self)

# ---------------------------------------------------------------------------
class Configuration(object):
    
    # ----------------------------------------------------------------------
    def __init__( self, 
                  dependencies=None, 
                  version_specs=None,
                  description=None,
                ):
        self.Dependencies                   = dependencies or []
        self.VersionSpecs                   = version_specs or VersionSpecs([], {})
        self.Description                    = description
        # self.Fingerprint is added during SetupEnvironment

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjStrImpl(self)
