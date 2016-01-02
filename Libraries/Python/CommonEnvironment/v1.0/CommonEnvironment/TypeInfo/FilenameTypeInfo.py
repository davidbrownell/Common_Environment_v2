# ---------------------------------------------------------------------------
# |  
# |  FilenameTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/26/2015 10:16:30 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import itertools
import os
import sys

from .Impl.FundamentalTypeInfo import FundamentalTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class FilenameTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "Filename"
    PythonItemRegularExpressionStrings      = ".+"

    _type_counter = itertools.count()

    Type_File                               = _type_counter.next()
    Type_Directory                          = _type_counter.next()
    Type_Either                             = _type_counter.next()

    del _type_counter

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type=Type_File,
                  ensure_exists=True,
                  **type_info_args
                ):
        super(FilenameTypeInfo, self).__init__(**type_info_args)

        self.Type                           = type
        self.EnsureExists                   = ensure_exists

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if not self.EnsureExists:
            return ''

        return "Value must be a valid {} name".format(self._TypeToString(self.Type))

    @property
    def PythonDefinitionString(self):
        return "{name}({super}, type=FilenameTypeInfo.{type}, ensure_exists={ensure_exists})" \
                    .format( name=self.__class__.__name__,
                             super=self._PythonDefinitionStringContents,
                             type=self._TypeFlagToString(self.Type),
                             ensure_exists=self.EnsureExists,
                           )

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return os.path.realpath(os.path.normpath(item))

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        if not self.EnsureExists:
            return

        if self.Type == self.Type_File:
            validator = os.path.isfile
        elif self.Type == self.Type_Directory:
            validator = os.path.isdir
        elif self.Type == self.Type_Either:
            validator = os.path.exists
        else:
            assert False

        if not validator(item):
            return "'{}' is not a valid {}".format(item, self._TypeToString(self.Type))

    # ---------------------------------------------------------------------------
    @classmethod
    def _TypeToString(cls, type):
        if type == cls.Type_File:
            return "file"

        if type == cls.Type_Directory:
            return "directory"

        if type == cls.Type_Either:
            return "file or directory"

        assert False

    # ---------------------------------------------------------------------------
    @classmethod
    def _TypeFlagToString(cls, type):
        if type == cls.Type_File:
            return "Type_File"

        if type == cls.Type_Directory:
            return "Type_Directory"

        if type == cls.Type_Either:
            return "Type_Either"

        assert False

# ---------------------------------------------------------------------------
class DirectoryTypeInfo(FilenameTypeInfo):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  ensure_exists=True,
                  **type_info_args
                ):
        super(DirectoryTypeInfo, self).__init__( type=self.Type_Directory,
                                                 ensure_exists=ensure_exists,
                                                 **type_info_args
                                               )
