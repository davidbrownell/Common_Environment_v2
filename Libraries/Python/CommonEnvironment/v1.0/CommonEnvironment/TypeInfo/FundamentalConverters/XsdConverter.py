# ----------------------------------------------------------------------
# |  
# |  XsdConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-04-24 20:31:37
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
import textwrap

from collections import OrderedDict

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import RegularExpression
from CommonEnvironment.TypeInfo.FundamentalTypes import Visitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class XsdConverter(Visitor):
    # ----------------------------------------------------------------------
    @staticmethod
    def OnBool(type_info):
        return "xs:boolean"

    # ----------------------------------------------------------------------
    @staticmethod
    def OnDateTime(type_info):
        return "xs:dateTime"
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnDate(type_info):
        return "xs:date"
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnDuration(type_info):
        return "xs:duration"
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnEnum(type_info):
        return textwrap.dedent(
            """\
            <xs:restriction base="xs:string">
            {}
            </xs:restriction>
            """).format('\n'.join([ '    <xs:enumeration value="{}" />'.format(value) for value in type_info.Values ]))
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnFilename(type_info):
        return textwrap.dedent(
            """\
            <xs:restriction base="xs:string">
                <xs:minLength value="1" />
            </xs:restriction>
            """)
    
    # ----------------------------------------------------------------------
    @classmethod
    def OnDirectory(cls, type_info):
        return cls.OnFilename(type_info)

    # ----------------------------------------------------------------------
    @staticmethod
    def OnFloat(type_info):
        restrictions = OrderedDict()

        if type_info.Min != None:
            restrictions["minInclusive"] = type_info.Min
       
        if type_info.Max != None:
            restrictions["maxInclusive"] = type_info.Max
       
        if not restrictions:
            return "xs:decimal"
       
        return textwrap.dedent(
            """\
            <xs:restriction base="xs:decimal">
            {}
            </xs:restriction>
            """).format('\n'.join([ '    <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in restrictions.iteritems() ]))
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnGuid(type_info):
        return textwrap.dedent(
            """\
            <xs:restriction base="xs:string">
                <xs:pattern value="%s" />
            </xs:restriction>
            """) % GuidTypeInfo().PythonItemRegularExpressionString
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnInt(type_info):
        type = None

        if type_info.Bytes == None:
            type = "integer"
        elif type_info.Bytes == 1:
            type = "byte"
        elif type_info.Bytes == 2:
            type = "short"
        elif type_info.Bytes == 4:
            type = "int"
        elif type_info.Bytes == 8:
            type = "long"
        else:
            assert False, type_info.Bytes
    
        restrictions = OrderedDict()
    
        if type_info.Min != None:
            if type_info.Min == 0:
                type = "nonNegative{}{}".format(type[0].upper(), type[1:])
            else:
                restrictions["minInclusive"] = type_info.Min
    
        if type_info.Max != None:
            if type_info.Max == 0:
                type = "negative{}{}".format(type[0].upper(), type[1:])
            else:
                restrictions["maxInclusive"] = type_info.Max
    
        if not restrictions:
            return "xs:{}".format(type)
    
        return textwrap.dedent(
            """\
            <xs:restriction base="xs:{}">
            {}
            </xs:restriction>
            """).format( type,
                         '\n'.join([ '    <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in restrictions.iteritems() ]),
                       )
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnString(type_info):
        restrictions = OrderedDict()

        if type_info.ValidationExpression != None:
            restrictions["pattern"] = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)
                        
        else:
            if type_info.MinLength not in [ None, 0, ]:
                restrictions["minLength"] = type_info.MinLength
                    
            if type_info.MaxLength != None:
                restrictions["maxLength"] = type_info.MaxLength
                    
        if not restrictions:
            return "xs:string"
                    
        return textwrap.dedent(
            """\
            <xs:restriction base="xs:string">
            {}
            </xs:restriction>
            """).format('\n'.join([ '    <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in restrictions.iteritems() ]))

    # ----------------------------------------------------------------------
    @staticmethod
    def OnTime(type_info):
        return "xs:time"
