# ---------------------------------------------------------------------------
# |  
# |  DateTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/27/2015 10:47:23 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import os
import sys

from .Impl.FundamentalTypeInfo import FundamentalTypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <Wrong hanging indentation> pylint: disable = C0330

class DateTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = datetime.date
    Desc                                    = "Date"
    ConstraintsDesc                         = ''
    
    _sep = r"[-/\.]"

    PythonItemRegularExpressionStrings      = [ expr % { "sep" : _sep, 
                                                         "suffix" : index,
                                                       } 
                                                for index, expr in enumerate([ # Ordered from most- to lease-specific in the hopes of minimizing ambiguity
                                                                             
                                                                               # YYYY-MM-DD
                                                                               r"(?P<year%(suffix)s>[0-9]{4})%(sep)s(?P<month%(suffix)s>(0?[1-9]|1[0-2]))%(sep)s(?P<day%(suffix)s>([0-2][0-9]|3[0-1]))",
                                                                             
                                                                               # MM-DD-YYYY
                                                                               r"(?P<month%(suffix)s>(0?[1-9]|1[0-2]))%(sep)s(?P<day%(suffix)s>([0-2][0-9]|3[0-1]))%(sep)s(?P<year%(suffix)s>[0-9]{4})",
                                                                             
                                                                               # YY-MM-DD
                                                                               r"(?P<year%(suffix)s>\d{2})%(sep)s(?P<month%(suffix)s>(0?[1-9]|1[0-2]))%(sep)s(?P<day%(suffix)s>([0-2][0-9]|3[0-1]))",
                                                                             
                                                                               # MM-DD-YY
                                                                               r"(?P<month%(suffix)s>(0?[1-9]|1[0-2]))%(sep)s(?P<day%(suffix)s>([0-2][0-9]|3[0-1]))%(sep)s(?P<year%(suffix)s>\d{2})",
                                                                             ])
                                              ]
    
    del _sep

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.date.today()
        
    # ---------------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "DateTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(item):
        return item

    # ----------------------------------------------------------------------
    @classmethod
    def ItemFromRegexMatch(cls, string, regex_match, regex_string_index):
        year = int(regex_match.group("year{}".format(regex_string_index)))
        month = int(regex_match.group("month{}".format(regex_string_index)))
        day = int(regex_match.group("day{}".format(regex_string_index)))

        if year < 100:
            # Assume that the year applies to the current century. This could lead
            # to ambiguity late in each century :)
            year = (datetime.datetime.now().year / 100) * 100 + year

        return datetime.date( year=year,
                              month=month,
                              day=day,
                            )

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
