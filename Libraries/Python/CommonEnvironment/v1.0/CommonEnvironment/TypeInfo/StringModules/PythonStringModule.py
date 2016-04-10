# ---------------------------------------------------------------------------
# |  
# |  PythonStringModule.py
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
import sys
import uuid

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.TypeInfo import StringModules

from ..FundamentalTypes import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@staticderived
class PythonStringModule(StringModules.StringModule):
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

    # ---------------------------------------------------------------------------
    @classmethod
    def ToString(cls, type_info, item):
        type_info_type = type(type_info)

        if type_info_type in [ StringTypeInfo, EnumTypeInfo, ]:
            return item
        
        if type_info_type in [ IntTypeInfo, FloatTypeInfo, GuidTypeInfo, ]:
            return str(item)

        if type_info_type in [ FilenameTypeInfo, DirectoryTypeInfo, ]:
            return item.replace(os.path.sep, '/')

        if type_info_type == BoolTypeInfo:
            return "true" if item else "false"

        if type_info_type in [ DateTimeTypeInfo, DateTypeInfo, TimeTypeInfo, ]:
            args = {}
            
            if type_info_type == DateTimeTypeInfo:
                args["sep"] = ' '
                
            return item.isoformat(**args)

        if type_info_type == DurationTypeInfo:
            seconds = item.total_seconds()

            hours = int(seconds / (60 * 60))
            seconds %= (60 * 60)

            minutes = int(seconds / 60)
            seconds %= 60

            return "{hours}:{minutes:02}:{seconds:02}".format(**locals())
                
        assert False, ("Unexpected", type_info_type)

    # ---------------------------------------------------------------------------
    @classmethod
    def FromString(cls, type_info, string, regex_match, regex_string_index):
        type_info_type = type(type_info)

        if type_info_type in [ StringTypeInfo, EnumTypeInfo, ]:
            return string

        if type_info_type == IntTypeInfo:
            return int(string)

        if type_info_type == FloatTypeInfo:
            return float(string)

        if type_info_type in [ FilenameTypeInfo, DirectoryTypeInfo, ]:
            return string.replace('/', os.path.sep)

        if type_info_type == BoolTypeInfo:
            return string.lower() in [ "true", "t", "yes", "y", "1", ]

        if type_info_type == GuidTypeInfo:
            return uuid.UUID(string)

        if type_info_type == DateTimeTypeInfo:
            return datetime.datetime.strptime(string, "%Y-%m-%d{sep}%H:%M{seconds}{fraction_seconds}{time_zone}" \
                        .format( sep='T' if 'T' in string else ' ',
                                 seconds=":%S" if string.count(':') > 1 else '',
                                 fraction_seconds=".%f" if '.' in string else '',
                                 time_zone="%z" if '+' in string else '',
                               ))

        if type_info_type == DateTypeInfo:
            return type_info.ItemFromRegexMatch(string, regex_match, regex_string_index)

        if type_info_type == TimeTypeInfo:
            return datetime.datetime.strptime(string, "%H:%M:%S{fraction_seconds}{time_zone}" \
                        .format( fraction_seconds=".%f" if '.' in string else '',
                                 time_zone="%z" if '+' in string else '',
                               )).time()

        if type_info_type == DurationTypeInfo:
            parts = string.split(':')

            if len(parts) > 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(float(parts[2]))
            else:
                hours = 0
                minutes = int(parts[0])
                seconds = int(float(parts[1]))

            return datetime.timedelta( hours=hours,
                                       minutes=minutes,
                                       seconds=seconds,
                                     )

        assert False, ("Unexpected", type_info_type)

    # ---------------------------------------------------------------------------
    @classmethod
    def GetItemRegularExpressions(cls, type_info):
        return super(cls, PythonStringModule).GetItemRegularExpressions(type_info) 
