# ----------------------------------------------------------------------
# |  
# |  SimpleSchemaConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 15:31:56
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

from CommonEnvironment.Interface import staticderived

from . import SchemaConverter
from .. import Visitor as VisitorBase

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class SimpleSchemaConveter(SchemaConverter):

    # ----------------------------------------------------------------------
    @staticmethod
    def Convert( type_info,
                 name=None,
                 brackets=None,             # ( lbracket, rbracket )
                 arity_override=None,
               ):

        brackets = brackets or ( '<', '>' )

        # ----------------------------------------------------------------------
        @staticderived
        class Visitor(VisitorBase):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info, *args, **kwargs):
                return "boolean"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info, *args, **kwargs):
                return "datetime"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info, *args, **kwargs):
                return "date"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDirectory(type_info, *args, **kwargs):
                return "filename", { "EnsureExists" : "must_exist", }, { "type" : '"directory"', }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info, *args, **kwargs):
                return "duration"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info, *args, **kwargs):
                return "enum", { "Values" : "values",
                                 "FriendlyValues" : "friendly_values",
                               }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info, *args, **kwargs):
                return "filename", { "EnsureExists" : "must_exist" }, { "type" : '"either"' if type_info.MatchAny else '"file"', }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info, *args, **kwargs):
                return "number", { "Min" : "min",
                                   "Max" : "max",
                                 }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info, *args, **kwargs):
                return "guid"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info, *args, **kwargs):
                return "integer", { "Min" : "min",
                                    "Max" : "max",
                                    "Bytes" : "bytes",
                                  }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info, *args, **kwargs):
                return "string", { "ValidationExpression" : "validation_expression",
                                   "MinLength" : "min_length",
                                   "MaxLength" : "max_length",
                                 }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info, *args, **kwargs):
                return "time"

        # ----------------------------------------------------------------------
        
        result = Visitor.Accept(type_info)

        if isinstance(result, tuple):
            type_ = result[0]
            dynamic_attributes = result[1]

            if len(result) > 2:
                static_attributes = result[2]
            else:
                static_attributes = {}

            attributes = []

            for attribute_name, simple_schema_name in dynamic_attributes.iteritems():
                value = getattr(type_info, attribute_name, None)
                if value != None:
                    if isinstance(value, list):
                        value = "[ {} ]".format(', '.join([ '"{}"'.format(v) for v in value ]))
                    else:
                        value = '"{}"'.format(value)

                    attributes.append("{}={}".format(simple_schema_name, value))

            for simple_schema_name, value in static_attributes.iteritems():
                attributes.append("{}={}".format(simple_schema_name, value))

        else:
            type_ = result
            attributes = []
            
        if isinstance(arity_override, str):
            arity_string = arity_override
        else:
            arity_string = (arity_override or type_info.Arity).ToString(brackets=('{', '}'))

        return "{lbracket}{name}{type_}{attributes}{arity}{rbracket}" \
                    .format( lbracket=brackets[0],
                             rbracket=brackets[1],
                             name='' if not name else "{} ".format(name),
                             type_=type_,
                             attributes='' if not attributes else " {}".format(' '.join(attributes)),
                             arity='' if not arity_string else " {}".format(arity_string),
                           )
