# ---------------------------------------------------------------------------
# |  
# |  StandardStringModule.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/26/2015 05:29:14 PM
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
import re
import sys
import uuid

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment.TypeInfo import StringModules

from ..FundamentalTypes import *
from ..FundamentalTypes import Visitor as FundamentalTypesVisitor

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@staticderived
class StandardStringModule(StringModules.StringModule):
    # ---------------------------------------------------------------------------
    # |  Public Properties
    NoneString                              = "None"
    DefaultDelimiter                        = '|'

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def SplitString(value):
        for potential_delimiter in [ '|', ';', ',', ]:
            if potential_delimiter in value:
                return [ v.strip() for v in value.split(potential_delimiter) if v.strip() ]
                
        return [ value, ]

    # ----------------------------------------------------------------------
    @classmethod 
    def RegexInfo(cls, type_info):
        return cls._GetProcessor(type_info).RegexInfo(type_info)

    # ---------------------------------------------------------------------------
    @classmethod
    def ToString(cls, type_info, item):
        return cls._GetProcessor(type_info).ToString(item)

    # ----------------------------------------------------------------------
    @classmethod
    def FromString(cls, type_info, item, regex_match, regex_index):
        return cls._GetProcessor(type_info).FromString(item, regex_match, regex_index)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _GetProcessor(type_info):
        # ----------------------------------------------------------------------
        Processor                           = NamedTuple( "Processor",
                                                          "RegexInfo",
                                                          "ToString",
                                                          "FromString",
                                                        )

        # ----------------------------------------------------------------------
        @staticderived
        class Visitor(FundamentalTypesVisitor):
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info):
                return Processor(BoolRegexInfo, BoolToString, BoolFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info):
                return Processor(DateTimeRegexInfo, DateTimeToString, DateTimeFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info):
                return Processor(DateRegexInfo, DateToString, DateFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info):
                return Processor(DurationRegexInfo, DurationToString, DurationFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info):
                return Processor(EnumRegexInfo, EnumToString, EnumFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info):
                return Processor(FilenameRegexInfo, FilenameToString, FilenameFromString)

            # ----------------------------------------------------------------------
            @classmethod
            def OnDirectory(cls, type_info):
                return Processor(DirectoryRegexInfo, DirectoryToString, DirectoryFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info):
                return Processor(FloatRegexInfo, FloatToString, FloatFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info):
                return Processor(GuidRegexInfo, GuidToString, GuidFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info):
                return Processor(IntRegexInfo, IntToString, IntFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info):
                return Processor(StringRegexInfo, StringToString, StringFromString)

            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info):
                return Processor(TimeRegexInfo, TimeToString, TimeFromString)

        # ----------------------------------------------------------------------
        
        return Visitor.Accept(type_info)

# ----------------------------------------------------------------------
def BoolRegexInfo(type_info):
    return ( "({})".format( '|'.join([ "true", "t", "yes", "y", "1",
                                       "false", "f", "no", "n", "0",
                                     ])),
             re.IGNORECASE
           )

def BoolToString(item):
    return "true" if item else "false"

def BoolFromString(item, regex_match, regex_index):
    return item.lower() in [ "true", "t", "yes", "y", "1", ]

# ----------------------------------------------------------------------
def DateTimeRegexInfo(type_info):
    return "{}.{}".format(DateRegexInfo(type_info)[0], TimeRegexInfo(type_info))

def DateTimeToString(item):
    return item.isoformat(sep=' ')

def DateTimeFromString(item, regex_match, regex_index):
    return datetime.datetime.strptime(item, "%Y-%m-%d{sep}%H:%M{seconds}{fraction_seconds}{time_zone}" \
            .format( sep='T' if 'T' in item else ' ',
                     seconds=":%S" if item.count(':') > 1 else '',
                     fraction_seconds=".%f" if '.' in item else '',
                     time_zone="%z" if '+' in item else '',
                   ))

# ----------------------------------------------------------------------
def DateRegexInfo(type_info):
    sep = r"[-/\.]"

    return [ expr % { "sep" : sep, 
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

def DateToString(item):
    return item.isoformat()

def DateFromString(item, regex_match, regex_index):
    year = int(regex_match.group("year{}".format(regex_index)))
    month = int(regex_match.group("month{}".format(regex_index)))
    day = int(regex_match.group("day{}".format(regex_index)))

    if year < 100:
        # Assume that the year applies to the current century. This could lead
        # to ambiguity late in each century :)
        year = (datetime.datetime.now().year / 100) * 100 + year

    return datetime.date( year=year,
                          month=month,
                          day=day,
                        )

# ----------------------------------------------------------------------
def DurationRegexInfo(type_info):
    return r"([1-9][0-9]*|0)?:[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?"

def DurationToString(item):
    seconds = item.total_seconds()

    hours = int(seconds / (60 * 60))
    seconds %= (60 * 60)

    minutes = int(seconds / 60)
    seconds %= 60

    return "{hours}:{minutes:02}:{seconds:02}".format(**locals())

def DurationFromString(item, regex_match, regex_index):
    parts = item.split(':')

    if len(parts) > 2:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(float(parts[2]))
    else:
        hours = 0
        minutes = int(parts[0])
        seconds = int(parts[1])

    return datetime.timedelta( hours=hours,
                               minutes=minutes,
                               seconds=seconds,
                             )

# ----------------------------------------------------------------------
def EnumRegexInfo(type_info):
    return "({})".format('|'.join([ re.escape(value) for value in type_info.Values ]))

def EnumToString(item):
    return item

def EnumFromString(item, regex_match, regex_index):
    return item

# ----------------------------------------------------------------------
def FilenameRegexInfo(type_info):
    return r".+"

def FilenameToString(item):
    return item.replace(os.path.sep, '/')

def FilenameFromString(item, regex_match, regex_index):
    return item.replace('/', os.path.sep)

# ----------------------------------------------------------------------
def DirectoryRegexInfo(type_info):
    return FilenameRegexInfo(type_info)

def DirectoryToString(item):
    return FilenameToString(item)

def DirectoryFromString(item, regex_match, regex_index):
    return FilenameFromString(item, regex_match, regex_index)

# ----------------------------------------------------------------------
def FloatRegexInfo(type_info):
    prefix_regex = IntRegexInfo(type_info)

    if type_info.Min != None and type_info.Max != None and type_info.Min >= -1.0 and type_info.Max <= 1.0:
        prefix_regex = "({})?".format(prefix_regex)

    return r"{}\.[0-9]+".format(prefix_regex)

def FloatToString(item):
    return str(item)

def FloatFromString(item, regex_match, regex_index):
    return float(item)

# ----------------------------------------------------------------------
def GuidRegexInfo(type_info):
    d = { "char" : r"[0-9A-Fa-f]", }

    concise_regex = "%(char)s{32}" % d
    verbose_regex = "%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % d

    return [ r"\{%s\}" % verbose_regex,
             verbose_regex,
             r"\{%s\}" % concise_regex,
             concise_regex,
           ]

def GuidToString(item):
    return str(item)

def GuidFromString(item, regex_match, regex_index):
    return uuid.UUID(item)

# ----------------------------------------------------------------------
def IntRegexInfo(type_info):
    patterns = []

    if type_info.Min == None or type_info.Min < 0:
        patterns.append('-')

        if type_info.Max == None or type_info.Max > 0:
            patterns.append('?')

    patterns.append("[0-9]")
    
    if type_info.Min == None or type_info.Max == None:
        patterns.append('+')
    else:
        value = 10
        count = 1

        while True:
            if ( (type_info.Min == None or type_info.Min > -value) and 
                 (type_info.Max == None or type_info.Max < value)
               ):
                break

            value *= 10
            count += 1

        patterns.append("{%d}" % count)

    return ''.join(patterns)

def IntToString(item):
    return str(item)

def IntFromString(item, regex_match, regex_index):
    return int(item)

# ----------------------------------------------------------------------
def StringRegexInfo(type_info):
    if type_info.ValidationExpression:
        return type_info.ValidationExpression
        
    if type_info.MinLength == 1 and type_info.MaxLength == None:
        return ".+"

    if type_info.MinLength in [ 0, None, ] and type_info.MaxLength == None:
        return ".*"

    if type_info.MinLength != None and (type_info.MaxLength == None or type_info.MinLength == type_info.MaxLength):
        return ".{%d}" % (type_info.MinLength)

    if type_info.MinLength != None and type_info.MaxLength != None:
        return ".{%d,%d}" % (type_info.MinLength, type_info.MaxLength)

    return r".*"

def StringToString(item):
    return item

def StringFromString(item, regex_match, regex_index):
    return item

# ----------------------------------------------------------------------
def TimeRegexInfo(type_info):
    return r"([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(\+[0-9]+:[0-9]+)?"

def TimeToString(item):
    return item.isoformat()

def TimeFromString(item, regex_match, regex_index):
    return datetime.datetime.strptime(item, "%H:%M:%S{fraction_seconds}{time_zone}" \
                    .format( fraction_seconds=".%f" if '.' in item else '',
                             time_zone="%z" if '+' in item else '',
                           )).time()
