# ----------------------------------------------------------------------
# |  
# |  SimpleSchemaConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-04-27 08:30:07
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

from collections import OrderedDict

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.TypeInfo.FundamentalTypes import Visitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class SimpleSchemaConverter(Visitor):
    # ----------------------------------------------------------------------
    @classmethod
    def OnBool(cls, type_info, brackets=None):
        return cls._Create("boolean", type_info, brackets=brackets)

    # ----------------------------------------------------------------------
    @classmethod
    def OnDateTime(cls, type_info, brackets=None):
        return cls._Create("datetime", type_info, brackets=brackets)
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnDate(cls, type_info, brackets=None):
        return cls._Create("date", type_info, brackets=brackets)
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnDuration(cls, type_info, brackets=None):
        return cls._Create("duration", type_info, brackets=brackets)
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnEnum(cls, type_info, brackets=None):
        return cls._Create( "enum",
                            type_info,
                            { "Values" : "values",
                              "FriendlyValues" : "friendly_values",
                            },
                            brackets=brackets,
                          )
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnFilename(cls, type_info, brackets=None):
        if type_info.Type == FilenameTypeInfo.Type_File:
            type_ = "file"
        elif type_info.Type == FilenameTypeInfo.Type_Directory:
            type_ = "directory"
        elif type_info.Type == FilenameTypeInfo.Type_Either:
            type_ = "either"
        else:
            assert False, type_info.Type

        return cls._Create( "filename",
                            type_info,
                            { "EnsureExists" : "must_exist",
                            },
                            { "type" : '"{}"'.format(type_),
                            },
                            brackets=brackets,
                          )
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnFloat(cls, type_info, brackets=None):
        return cls._Create( "number",
                            type_info,
                            { "Min" : "min",
                              "Max" : "max",
                            },
                            brackets=brackets,
                          )
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnGuid(cls, type_info, brackets=None):
        return cls._Create("guid", type_info, brackets=brackets)
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnInt(cls, type_info, brackets=None):
        return cls._Create( "integer",
                            type_info,
                            { "Min" : "min",
                              "Max" : "max",
                              "Bytes" : "bytes",
                            },
                            brackets=brackets,
                          )
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnString(cls, type_info, brackets=None):
        return cls._Create( "string",
                            type_info,
                            { "ValidationExpression" : "validation_expression",
                              "MinLength" : "min_length",
                              "MaxLength" : "max_length",
                            },
                            brackets=brackets,
                          )

    # ----------------------------------------------------------------------
    @classmethod
    def OnTime(cls, type_info, brackets=None):
        return cls._Create("time", type_info, brackets=brackets)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Create( type_,
                 type_info,
                 attributes=None,
                 attribute_overrides=None,
                 brackets=None,             # ( lbracket, rbracket )
               ):
        params = []

        attribute_overrides = attribute_overrides or {}
        brackets = brackets or ( '<', '>' )

        for attribute_name, ss_name in (attributes or {}).iteritems():
            if ss_name in attribute_overrides:
                continue

            value = getattr(type_info, attribute_name, None)
            if value != None:
                if isinstance(value, list):
                    value = "[ {} ]".format(', '.join([ '"{}"'.format(v) for v in value ]))
                else:
                    value = '"{}"'.format(value)

                params.append("{}={}".format(ss_name, value))

        for k, v in attribute_overrides.iteritems():
            params.append("{}={}".format(k, v))

        arity = type_info.Arity.ToString()

        return "{}{{}} {}{}{}{}".format( brackets[0],
                                         type_,
                                         '' if not params else ' {}'.format(' '.join(params)),
                                         '' if not arity else ' {}'.format(arity),
                                         brackets[1],
                                       )
