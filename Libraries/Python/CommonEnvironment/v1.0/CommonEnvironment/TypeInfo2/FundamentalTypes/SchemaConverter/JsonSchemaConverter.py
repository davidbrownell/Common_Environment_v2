# ----------------------------------------------------------------------
# |  
# |  JsonSchemaConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 15:08:25
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
from CommonEnvironment import RegularExpression

from . import SchemaConverter

from .. import ( DateTypeInfo,
                 DurationTypeInfo,
                 GuidTypeInfo,
                 TimeTypeInfo,
                 Visitor as VisitorBase,
               )

from ..Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class JsonSchemaConverter(SchemaConverter):

    # ----------------------------------------------------------------------
    @staticmethod
    def Convert(type_info):
        # ----------------------------------------------------------------------
        @staticderived
        class Visitor(VisitorBase):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info, *args, **kwargs):
                return { "type" : "boolean", }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info, *args, **kwargs):
                return { "type" : "string",
                         "format" : "date-time",
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(DateTypeInfo()))),
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDirectory(type_info, *args, **kwargs):
                return { "type" : "string",
                         "minLength" : 1,
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(DurationTypeInfo()))),
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info, *args, **kwargs):
                return { "enum" : type_info.Values, }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info, *args, **kwargs):
                return { "type" : "string",
                         "minLength" : 1,
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info, *args, **kwargs):
                result = { "type" : "number", }

                for attribute, json_schema_key in [ ( "Min", "minimum" ),
                                                    ( "Max", "maximum" ),
                                                  ]:
                    value = getattr(type_info, attribute)
                    if value != None:
                        result[json_schema_key] = value

                return result
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(GuidTypeInfo()))),
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info, *args, **kwargs):
                result = { "type" : "integer", }

                for attribute, json_schema_key in [ ( "Min", "minimum" ),
                                                    ( "Max", "maximum" ),
                                                  ]:
                    value = getattr(type_info, attribute)
                    if value != None:
                        result[json_schema_key] = value

                return result
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info, *args, **kwargs):
                result = { "type" : "string", }

                if type_info.ValidationExpression != None:
                    validation = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)

                    if validation[0] != '^': validation = "^{}".format(validation)
                    if validation[-1] != '$': validation = "{}$".format(validation)

                    result["pattern"] = validation

                else:
                    if type_info.MinLength not in [ 0, None, ]:
                        result["minLength"] = type_info.MinLength

                    if type_info.MaxLength:
                        result["maxLength"] = type_info.MaxLength

                return result
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(TimeTypeInfo()))),
                       }

        # ----------------------------------------------------------------------
        
        result = Visitor.Accept(type_info)

        if type_info.Arity.IsCollection:
            result = { "type" : "array",
                       "items" : result,
                     }

            if type_info.Arity.Min != 0:
                result["minItems"] = type_info.Arity.Min

            if type_info.Arity.Max != None:
                result["maxItems"] = type_info.Arity.Max

        return result
