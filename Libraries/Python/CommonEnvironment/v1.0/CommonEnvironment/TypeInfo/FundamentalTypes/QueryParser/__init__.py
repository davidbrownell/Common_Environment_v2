# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-01-17 07:38:21
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
import os
import re
import sys

import antlr4

from CommonEnvironment import Antlr4Helpers
from CommonEnvironment.Antlr4Helpers.ErrorListener import ErrorListener
from CommonEnvironment.CallOnExit import CallOnExit

from CommonEnvironment.TypeInfo import FundamentalTypes
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Class '<name>' has no '<attr>' member> pylint: disable = E1103

# <Unused import> pylint: disable = W0611
# <Unused variable> pylint: disable = W0612
# <Unused argument> pylint: disable = W0613
# <Redefinig built-in type> pylint: disable = W0622

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Expression(object):
    """Abstract base class for Expression objects"""

# ----------------------------------------------------------------------
class StandardExpression(Expression):
    def __init__(self, var_name, type_info, operator, rhs):
        self.LHS                            = var_name
        self.TypeInfo                       = type_info
        self.Operator                       = operator
        self.RHS                            = rhs

# ----------------------------------------------------------------------
class AndExpression(Expression):
    def __init__(self, lhs, rhs):
        self.LHS                            = lhs
        self.RHS                            = rhs

# ----------------------------------------------------------------------
class OrExpression(Expression):
    def __init__(self, lhs, rhs):
        self.LHS                            = lhs
        self.RHS                            = rhs

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def ParseFactory( string_serialization=None,
                  **variables               # { <var_name> : <type_info>, }
                ):
    AntlrException = ErrorListener.AntlrException

    string_serialization = string_serialization or StringSerialization

    Parser = Antlr4Helpers.CreateParser( os.path.join(_script_dir, "Grammars", "GeneratedCode"),
                                         "QueryParser",
                                       )

    # ----------------------------------------------------------------------
    class Visitor(Parser.Visitor):
        # ----------------------------------------------------------------------
        def __init__(self):
            self.root = []
            self.stack = []

            self._time_delta_parser = re.compile(r"^(?P<value>\d+)(?P<unit>[A-Za-z]+)$")

        # ----------------------------------------------------------------------
        def visitStatements(self, ctx):
            return self.visitChildren(ctx)
    
        # ----------------------------------------------------------------------
        def visitExpression(self, ctx):
            if len(ctx.children) == 1:
                return self.visitChildren(ctx)

            assert len(ctx.children) == 3, ctx.children

            # LHS
            self.visit(ctx.children[0])
            assert self.stack
            lhs = self.stack.pop()

            # RHS
            self.visit(ctx.children[2])
            assert self.stack
            rhs = self.stack.pop()

            expression = None

            if ctx.children[1].symbol.type == Parser.AND:
                expression = AndExpression(lhs, rhs)
            elif ctx.children[1].symbol.type == Parser.OR:
                expression = OrExpression(lhs, rhs)
            else:
                assert False, ctx.children[1]
    
            assert expression
            self.stack.append(expression)

        # ----------------------------------------------------------------------
        def visitAtom(self, ctx):
            assert len(ctx.children) == 3, ctx.children

            if ctx.children[0].symbol.type == Parser.LPAREN:
                assert ctx.children[2].symbol.type == Parser.RPAREN, ctx.children[2]

                return self.visit(ctx.children[1])

            # Get the LHS
            assert ctx.children[0].symbol.type == Parser.ID, ctx.children[0]

            lhs = ctx.children[0].symbol.text
            if lhs not in variables:
                raise AntlrException.Create(ctx.children[0].symbol, "'{}' is not a valid variable name".format(lhs))

            type_info = variables[lhs]
            
            self.stack.append(type_info)
            with CallOnExit(self.stack.pop):
                # Get the RHS
                self.visit(ctx.children[2])

                assert self.stack
                rhs = self.stack.pop()

            # Get the operator
            symbol = ctx.children[1].symbol
            
            # Verify allowed operations

            # ----------------------------------------------------------------------
            class Visitor(FundamentalTypes.Visitor):
                # ----------------------------------------------------------------------
                @classmethod
                def OnBool(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnDateTime(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnDate(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnDirectory(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                          Parser.LIKE,
                                          Parser.UNDER,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnDuration(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnEnum(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnFilename(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                          Parser.LIKE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnFloat(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnGuid(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnInt(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnString(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                          Parser.LIKE,
                                        )
            
                # ----------------------------------------------------------------------
                @classmethod
                def OnTime(cls, type_info, *args, **kwargs):
                    return cls._Validate( Parser.EQUAL,
                                          Parser.NOT_EQUAL,
                                          Parser.LT,
                                          Parser.LTE,
                                          Parser.GT,
                                          Parser.GTE,
                                        )

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                @staticmethod
                def _Validate(*acceptable_types):
                    if symbol.type not in acceptable_types:
                        raise AntlrException.Create(symbol, "'{}' is not a valid operator for '{}' types".format(symbol.text, type_info.Desc))
                     
            # ----------------------------------------------------------------------
            
            Visitor.Accept(type_info)

            self.stack.append(StandardExpression(lhs, type_info, symbol.text, rhs))

        # ----------------------------------------------------------------------
        def visitValue(self, ctx):
            # Get the initial value
            symbol = ctx.children[0].symbol

            assert self.stack
            type_info = self.stack[-1]
    
            if symbol.type == Parser.INT:
                value = int(symbol.text)
            
            elif symbol.type == Parser.NUMBER:
                value = float(symbol.text)
            
            elif symbol.type in [ Parser.DOUBLE_QUOTE_STRING, Parser.SINGLE_QUOTE_STRING, ]:
                try:
                    value = string_serialization.DeserializeItem(type_info, symbol.text[1:-1])    
                except Exception, ex:
                    raise AntlrException.Create(symbol, str(ex))
            
            elif symbol.type == Parser.TODAY:
                if isinstance(type_info, FundamentalTypes.DateTimeTypeInfo):
                    value = datetime.datetime.now().replace( hour=0,
                                                             minute=0,
                                                             second=0,
                                                             microsecond=0,
                                                           )
                elif isinstance(type_info, FundamentalTypes.DateTypeInfo):
                    value = datetime.date.today()
                else:
                    raise AntlrException.Create( symbol,
                                                 "'{}' types do not support '{}' variables".format( type_info.Desc,
                                                                                                    Parser.GetLiteral(Parser.TODAY),
                                                                                                  ))
                
            
            elif symbol.type == Parser.NOW:
                if isinstance(type_info, FundamentalTypes.DateTimeTypeInfo):
                    value = datetime.datetime.now()
                elif isinstance(type_info, FundamentalTypes.DateTypeInfo):
                    value = datetime.date.today()
                elif isinstance(type_info, FundamentalTypes.TimeTypeInfo):
                    value = datetime.datetime.now().time()
                else:
                    raise AntlrException.Create( symbol, 
                                                 "'{}' types do not support '{}' variables".format( type_info.Desc,
                                                                                                    Parser.GetLiteral(Parser.NOW),
                                                                                                  ))
            
            else:
                assert False, symbol.type
            
            if len(ctx.children) == 3:
                # Get the time delta
                symbol = ctx.children[2].symbol

                match = self._time_delta_parser.match(symbol.text)
                assert match, symbol.text

                delta_value = int(match.group("value"))
                delta_unit = match.group("unit")

                if delta_unit == 'Y':
                    delta = datetime.timedelta(weeks=52 * delta_value)
                elif delta_unit == 'W':
                    delta = datetime.timedelta(weeks=delta_value)
                elif delta_unit == 'M':
                    delta = datetime.timedelta(days=31 * delta_value)
                elif delta_unit == 'D':
                    delta = datetime.timedelta(days=delta_value)
                elif delta_unit == 'h':
                    delta = datetime.timedelta(hours=delta_value)
                elif delta_unit == 'm':
                    delta = datetime.timedelta(minutes=delta_value)
                elif delta_unit == 's':
                    delta = datetime.timedelta(seconds=delta_value)
                elif delta_unit == 'mi':
                    delta = datetime.timedelta(microseconds=delta_value)
                else:
                    assert False, delta_unit

                # Get the operation
                symbol = ctx.children[1].symbol

                if symbol.text == '+':
                    value += delta
                elif symbol.text == '-':
                    value -= delta
                else:
                    assert False, symbol.text

            try:
                type_info.ValidateItem(value)
                self.stack.append(value)

                return
            except Exception, ex:
                raise AntlrException.Create(symbol, str(ex))

    # ----------------------------------------------------------------------
    def Func(s):

        visitor = Visitor()
        Parser.Parse(visitor, s)

        if len(visitor.stack) == 1:
            return visitor.stack[0]

        return visitor.stack

    # ----------------------------------------------------------------------
    
    return Func
