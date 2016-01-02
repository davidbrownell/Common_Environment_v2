# ---------------------------------------------------------------------------
# |  
# |  CreateRepositoryId.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/30/2015 04:40:42 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Creates a repository id file for a new repository.
"""

import os
import sys
import uuid

from CommonEnvironment import CommandLine
from CommonEnvironment import Package

__package__ = Package.CreateName(__package__, __name__, __file__)
from . import Impl

import __init__ as SourceRepositoryTools

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(),
                                  name=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def EntryPoint( output_dir,
                name,
                output_stream=sys.stdout,
              ):
    assert os.path.isdir(output_dir), output_dir

    filename = os.path.join(output_dir, SourceRepositoryTools.REPOSITORY_ID_FILENAME)
     
    with open(filename, 'w') as f:
        f.write(Impl.REPOSITORY_ID_CONTENT_TEMPLATE.format( name=name,
                                                            guid=str(uuid.uuid4()).replace('-', '').upper(),
                                                          ))

    output_stream.write("The file '{}' has been written.\n\n".format(filename))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
