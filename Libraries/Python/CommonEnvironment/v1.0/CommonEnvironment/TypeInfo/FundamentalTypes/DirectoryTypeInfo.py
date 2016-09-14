# ----------------------------------------------------------------------
# |  
# |  DirectoryTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-04 18:43:02
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class DirectoryTypeInfo(TypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "Directory"

    # ----------------------------------------------------------------------
    def __init__( self,
                  ensure_exists=True,
                  **type_info_args
                ):
        super(DirectoryTypeInfo, self).__init__(**type_info_args)

        self.EnsureExists                   = ensure_exists

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if not self.EnsureExists:
            return ''

        return "Value must be a valid directory"

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DirectoryTypeInfo({}, ensure_exists={})".format( self._PythonDefinitionStringContents,
                                                                 self.EnsureExists,
                                                               )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if not self.EnsureExists:
            return

        if not os.path.isdir(item):
            return "'{}' is not a valid directory".format(item)
