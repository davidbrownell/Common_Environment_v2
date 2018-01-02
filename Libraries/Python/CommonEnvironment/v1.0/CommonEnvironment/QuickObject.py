# ---------------------------------------------------------------------------
# |  
# |  QuickObject.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/08/2015 12:39:30 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------

import os
import sys

import six

from .StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable-msg = R0903
class QuickObject(object):
    """Create a quick object with named parameters.
    
       Usage:
          my_object = QuickObject(username="foo", password="bar")
          my_object.username = "changed"
          my_object.password = "values"
    """
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __str__(self):
        output = [ "QuickObject", ]

        for key, value in six.iteritems(self.__dict__):
            if isinstance(value, QuickObject):
                value = StreamDecorator.LeftJustify(str(value), 24)

            output.append("  % -20s: %s" % (key, value))

        return '\n'.join(output)
