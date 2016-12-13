# ----------------------------------------------------------------------
# |  
# |  StringSerialization.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 08:02:02
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
import os
import re
import sys
import uuid

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import RegularExpression

from . import Serialization

from .. import ( Visitor as FundamentalTypesVisitor, 
                 CreateSimpleVisitor,
                 DateTypeInfo,
                 TimeTypeInfo,
               )

from ... import ValidationException

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Wrong hanging indentation> pylint: disable = C0330

# ----------------------------------------------------------------------
@staticderived
class StringSerialization(Serialization):

    # ----------------------------------------------------------------------
    @classmethod
    def GetRegularExpressionString(cls, type_info):
        result = cls.GetRegularExpressionStringInfo(type_info)[0]

        if isinstance(result, tuple):
            result = result[0]

        return result

    # ----------------------------------------------------------------------
    @classmethod
    def GetRegularExpressionStringInfo(cls, type_info):
        
        # ----------------------------------------------------------------------
        class Visitor(FundamentalTypesVisitor):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info):
                return [ ( r"(true|t|yes|y|1|false|f|no|n|0)",
                           re.IGNORECASE,
                         ),
                       ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info):
                return [ "{}[ T]{}".format( cls.GetRegularExpressionString(DateTypeInfo()),
                                            cls.GetRegularExpressionString(TimeTypeInfo()),
                                          ),
                       ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info):
                sep = r"[-/\.]"

                return [ expr % { "sep" : sep,
                                  "suffix" : index,
                                }
                         for index, expr in enumerate([ # YYYY-MM-DD
                                                        r"(?P<year%(suffix)s>[0-9]{4})%(sep)s(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])",

                                                        # MM-DD-YYYY
                                                        r"(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])%(sep)s(?P<year%(suffix)s>[0-9]{4})",

                                                        # YY-MM-DD
                                                        r"(?P<year%(suffix)s>\d{2})%(sep)s(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])",

                                                        # MM-DD-YY
                                                        r"(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])%(sep)s(?P<year%(suffix)s>\d{2})",
                                                      ])
                       ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDirectory(type_info):
                return [ r".+", ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info):
                return [ r"(?P<hours>[1-9][0-9]*|0):(?P<minutes>[0-5][0-9]):(?P<seconds>[0-5][0-9])(?:\.(?P<microseconds>[0-9]+))?",
                       ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info):
                return [ "({})".format('|'.join([ re.escape(value) for value in type_info.Values ])),
                       ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info):
                return [ r".+", ]
        
            # ----------------------------------------------------------------------
            @classmethod
            def OnFloat(this_cls, type_info):
                return [ r"{}\.[0-9]+".format(this_cls.OnInt(type_info)[0]), ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info):
                d = { "char" : r"[0-9A-Fa-f]", }

                concise = "%(char)s{32}" % d
                verbose = "%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % d

                return [ r"\{%s\}" % verbose,
                         verbose,
                         r"\{%s\}" % concise,
                         concise,
                       ]

            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info):
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

                    patterns.append("{1,%d}" % count)

                return [ ''.join(patterns), ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info):
                if type_info.ValidationExpression:
                    return [ RegularExpression.PythonToJavaScript(type_info.ValidationExpression), 
                           ]

                if type_info.MinLength in [ 0, None, ] and type_info.MaxLength == None:
                    return [ ".*", ]

                if type_info.MinLength == 1 and type_info.MaxLength == None:
                    return [ ".+", ]
                          
                assert type_info.MinLength != None
                assert type_info.MaxLength != None

                if type_info.MinLength == type_info.MaxLength:
                    return [ ".{%d}" % type_info.MinLength, ]

                return [ ".{%d,%d}" % (type_info.MinLength, type_info.MaxLength), ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info):
                return [ r"(?P<hour>[0-1][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])(?:\.(?P<microseconds>\d+))?(?:(?P<tz_utc>Z)|(?P<tz_sign>[\+\-])(?P<tz_hour>\d{2}):(?P<tz_minute>[0-5][0-9]))?",
                       ]

        # ----------------------------------------------------------------------
        
        return Visitor.Accept(type_info)

    # ----------------------------------------------------------------------
    @staticmethod
    def _SerializeItemImpl(type_info, item, **custom_args):
        
        # ----------------------------------------------------------------------
        @staticderived
        class Visitor(FundamentalTypesVisitor):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info):
                return str(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info):
                return item.isoformat(sep=custom_args.get("sep", ' '))
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info):
                return item.isoformat()
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDirectory(type_info):
                return item.replace(os.path.sep, '/')
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info):
                seconds = item.total_seconds()

                hours = int(seconds / (60 * 60))
                seconds %= (60 * 60)

                minutes = int(seconds / 60)
                seconds %= 60

                return "{hours}:{minutes:02}:{seconds:02.6f}".format(**locals())
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info):
                return item
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info):
                return item.replace(os.path.sep, '/')
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info):
                return str(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info):
                return str(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info):
                return str(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info):
                return item
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info):
                return item.isoformat()

        # ----------------------------------------------------------------------
        
        return Visitor.Accept(type_info)

    # ----------------------------------------------------------------------
    @classmethod
    def _DeserializeItemImpl(cls, type_info, item, **custom_kwargs):
        # custom_kwargs:
        #   type_info type      Key         Value       Default             Desc
        #   ------------------  ----------  ----------  ------------------  ----------------
        #   DirectoryTypeInfo   normalize   Boolean     True                Applies os.path.realpath and os.path.normpath to the string
        #   FilenameTypeInfo    normalize   Boolean     True                Applies os.path.realpath and os.path.normpath to the string

        match = None
        match_index = None

        for index, regex_info in enumerate(cls.GetRegularExpressionStringInfo(type_info)):
            if isinstance(regex_info, tuple):
                regex_string, regex_flags = regex_info
            else:
                regex_string = regex_info
                regex_flags = re.DOTALL | re.MULTILINE

            if not regex_string.startswith("^"):
                regex_string = "^{}".format(regex_string)
            if not regex_string.endswith("$"):
                regex_string = "{}$".format(regex_string)

            potential_match = re.match(regex_string, item, regex_flags)
            if potential_match:
                match = potential_match
                match_index = index

                break

        if not match:
            # ----------------------------------------------------------------------
            def OnTypeInfoWithStringAsBase(type_info):
                return "'{}' is not valid - {}".format(item, type_info.ConstraintsDesc)

            # ----------------------------------------------------------------------
            def OnDefault(type_info):
                return "'{}' is not a valid '{}' string".format(item, type_info.Desc)

            # ----------------------------------------------------------------------
            
            error = CreateSimpleVisitor( onEnumFunc=OnTypeInfoWithStringAsBase,
                                         onStringFunc=OnTypeInfoWithStringAsBase,
                                         onDefaultFunc=OnDefault,
                                       ).Accept(type_info)
            
            raise ValidationException(error)

        # ----------------------------------------------------------------------
        @staticderived
        class Visitor(FundamentalTypesVisitor):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info):
                return item.lower() in [ "true", "t", "yes", "y", "1", ]
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info):
                match_dict = match.groupdict()

                has_timezone = False
                for attribute_name in [ "tz_utc", "tz_hour", ]:
                    if match_dict.get(attribute_name, None) != None:
                        has_timezone = True
                        break
                
                return datetime.datetime.strptime(item, "%Y-%m-%d{sep}%H:%M{seconds}{fraction_seconds}{time_zone}" \
                                                            .format( sep='T' if 'T' in item else ' ',
                                                                     seconds=":%S" if item.count(':') > 1 else '',
                                                                     fraction_seconds=".%f" if '.' in item else '',
                                                                     time_zone="%z" if has_timezone else '',
                                                                   ))
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info):
                year = int(match.group("year{}".format(match_index)))
                month = int(match.group("month{}".format(match_index)))
                day = int(match.group("day{}".format(match_index)))

                if year < 100:
                    # Assume that the year applies to the current century. This could lead
                    # to ambiguity late in each century :)
                    year = (datetime.datetime.now().year / 100) * 100 + year

                return datetime.date( year=year,
                                      month=month,
                                      day=day,
                                    )
        
            # ----------------------------------------------------------------------
            @classmethod
            def OnDirectory(this_cls, type_info):
                return this_cls.OnFilename(type_info)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info):
                parts = item.split(':')

                if len(parts) == 3:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds_string = parts[2]

                elif len(parts) == 2:
                    hours = 0
                    minutes = int(parts[0])
                    seconds_string = parts[1]

                else:
                    assert False, item

                seconds_parts = seconds_string.split('.')
                if len(seconds_parts) == 2:
                    seconds = int(seconds_parts[0])
                    microseconds = int(seconds_parts[1])

                elif len(seconds_parts) == 1:
                    seconds = int(seconds_parts[0])
                    microseconds = 0

                else:
                    assert False, seconds_string

                return datetime.timedelta( hours=hours,
                                           minutes=minutes,
                                           seconds=seconds,
                                           microseconds=microseconds,
                                         )
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info):
                return item
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info):
                value = item.replace('/', os.path.sep)

                if custom_kwargs.get("normalize", True):
                    value = os.path.realpath(os.path.normpath(value))

                return value
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info):
                return float(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info):
                return uuid.UUID(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info):
                return int(item)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info):
                return item
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info):
                match_dict = match.groupdict()
                
                has_timezone = False
                for attribute_name in [ "tz_utc", "tz_hour", ]:
                    if match_dict.get(attribute_name, None) != None:
                        has_timezone = True
                        break
                
                return datetime.datetime.strptime(item, "%H:%M:%S{fraction_seconds}{time_zone}" \
                                                            .format( fraction_seconds=".%f" if '.' in item else '',
                                                                     time_zone="%z" if has_timezone else '',
                                                                   )).time()

        # ----------------------------------------------------------------------
        
        return Visitor.Accept(type_info)
