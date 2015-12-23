# ---------------------------------------------------------------------------
# |  
# |  Parse.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/27/2015 03:29:39 PM
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

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)   # <Redefining build-in type> pylint: disable = W0622

from .Observer import DefaultObserver

from .Impl.Populate import Populate
from .Impl.Validate import Validate
from .Impl.Transform import Transform

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def ParseFiles( filenames,
                observer=None,
              ):
    d = OrderedDict()

    for filename in filenames:
        d[filename] = lambda filename=filename: open(filename).read()

    return ParseEx(d, observer)

# ---------------------------------------------------------------------------
def ParseStrings( named_strings,            # { "<name>" : "<content>", }
                  observer=None,
                ):
    d = OrderedDict()

    for k, v in named_strings.iteritems():
        d[k] = lambda v=v: v

    return ParseEx(d, observer)

# ---------------------------------------------------------------------------
def ParseEx( source_name_content_generators,            # { "name" : def Func() -> content, }
             observer=None,
           ):
    observer = observer or DefaultObserver

    observer.VerifyFlags()

    root = Populate(source_name_content_generators, observer)
    root = Validate(root, observer)
    root = Transform(root, observer)

    # Eliminate the root element as the parent for top-level elements
    for child in root.Children:
        child.Parent = None

    return root.Children
