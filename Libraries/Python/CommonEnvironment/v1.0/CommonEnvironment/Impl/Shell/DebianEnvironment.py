# ----------------------------------------------------------------------
# |  
# |  DebianEnvironment.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-01-12 17:35:45
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import re
import sys
import uuid

from .LinuxEnvironmentImpl import LinuxEnvironmentImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class DebianEnvironment(LinuxEnvironmentImpl):
    Name                                    = "Debian"
    PotentialOSVersionDirectoryNames        = []
    
    # ---------------------------------------------------------------------------
    def __init__(self):
        super(DebianEnvironment, self).__init__()
        
        output_filename = "/tmp/{}".format(uuid.uuid4())
        
        # Version
        os.system('cat /etc/lsb-release > "{}"'.format(output_filename))
        with open(output_filename) as f: 
            content = f.read()
        os.remove(output_filename)
        
        match = re.search(r"DISTRIB_RELEASE=(?P<version>[\d\.]+)", content)
        assert match, content
        
        self._os_version = match.group("version")
        
        # Architecture
        os.system('uname -a > "{}"'.format(output_filename))
        with open(output_filename) as f: content = f.read()
        os.remove(output_filename)
        
        self._os_architecture = "x64" if "x86_64" in content else "x86"
        
    # ---------------------------------------------------------------------------
    @property
    def OSVersion(self):
        return self._os_version
        
    # ---------------------------------------------------------------------------
    @property
    def OSArchitecture(self):
        return self._os_architecture
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsActive(platform_name):
        return "debian" in platform_name
