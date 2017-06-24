# ----------------------------------------------------------------------
# |  
# |  XmlSchemaConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 16:02:40
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import textwrap

from collections import OrderedDict

import six

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import RegularExpression

from . import SchemaConverter

from ..FundamentalTypes import ( GuidTypeInfo,
                                 UriTypeInfo,
                                 Visitor as FundamentalVisitor,
                               )

from ..FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class XmlSchemaConverter(SchemaConverter):

    # ----------------------------------------------------------------------
    @staticmethod
    def Convert(type_info):
        # ----------------------------------------------------------------------
        @staticderived
        class Visitor(FundamentalVisitor):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info, *args, **kwargs):
                return "xs:boolean"
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info, *args, **kwargs):
                return "xs:dateTime"
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info, *args, **kwargs):
                return "xs:date"
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDirectory(type_info, *args, **kwargs):
                # TODO: ensure_exists
                return textwrap.dedent(
                    """\
                    <xs:restriction base="xs:string">
                      <xs:minLength value="1" />
                    </xs:restriction>
                    """)
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info, *args, **kwargs):
                return "xs:duration"
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info, *args, **kwargs):
                return textwrap.dedent(
                    """\
                    <xs:restriction base="xs:string">
                    {}
                    </xs:restriction>
                    """).format('\n'.join([ '  <xs:enumeration value="{}" />'.format(value) for value in type_info.Values ]))
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info, *args, **kwargs):
                # TODO: ensure_exists
                # TODO: match_directory
                return textwrap.dedent(
                    """\
                    <xs:restriction base="xs:string">
                      <xs:minLength value="1" />
                    </xs:restriction>
                    """)
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info, *args, **kwargs):
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
                    """).format('\n'.join([ '  <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in six.iteritems(restrictions) ]))
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info, *args, **kwargs):
                return textwrap.dedent(
                    """\
                    <xs:restriction base="xs:string">
                      <xs:pattern value="{}" />
                    </xs:restriction>
                    """).format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(GuidTypeInfo())))
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info, *args, **kwargs):
                type_ = None
                restrictions = OrderedDict()
                
                if type_info.Bytes == None:
                    type_ = "integer"
                elif type_info.Bytes == 1:
                    type_ = "byte"
                elif type_info.Bytes == 2:
                    type_ = "short"
                elif type_info.Bytes == 4:
                    type_ = "int"
                elif type_info.Bytes == 8:
                    type_ = "long"
                else:
                    assert False, type_info.Bytes

                if type_info.Min != None:
                    if type_info.Min >= 0:
                        type_ = "nonNegative{}{}".format(type_[0].upper(), type_[1:])
                        
                    if type_info.Min != 0 and not type_info.IsByteDefault:
                        restrictions["minInclusive"] = type_info.Min
                    
                if type_info.Max != None:
                    if type_info.Max < 0:
                        type_ = "negative{}{}".format(type_[0].upper(), type_[1:])
                    
                    if not type_info.IsByteDefault:
                        restrictions["maxInclusive"] = type_info.Max
                        
                if not restrictions:
                    return "xs:{}".format(type_)
                
                return textwrap.dedent(
                    """\
                    <xs:restrictions base="xs:{}">
                    {}
                    </xs:restrictions>
                    """).format(type_, '\n'.join([ '  <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in six.iteritems(restrictions) ]))

            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info, *args, **kwargs):
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
                    """).format('\n'.join([ '  <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in six.iteritems(restrictions) ]))
            
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info, *args, **kwargs):
                return "xs:time"

            # ----------------------------------------------------------------------
            @staticmethod
            def OnUri(type_info, *args, **kwargs):
                return textwrap.dedent(
                    """\
                    <xs:restriction base="xs:string">
                      <xs:pattern value="{}" />
                    </xs:restriction>
                    """).format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(UriTypeInfo())))
            
        # ----------------------------------------------------------------------
        
        return Visitor.Accept(type_info)
