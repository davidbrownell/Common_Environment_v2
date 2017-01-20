# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/15/2015 01:38:46 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import importlib
import os
import sys

import antlr4

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Constraints import FunctionConstraints
from CommonEnvironment.TypeInfo import FundamentalTypes

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
def GetLiteral(parser, value):
    value = parser.literalNames[value]

    if value[0] == "'":
        value = value[1:]

    if value[-1] == "'":
        value = value[:-1]

    return value

# ----------------------------------------------------------------------
@FunctionConstraints( antlr_output_dir=FundamentalTypes.DirectoryTypeInfo(),
                      name_prefix=FundamentalTypes.StringTypeInfo(),
                    )
def CreateParser( antlr_output_dir,
                  name_prefix,
                ):
    from .ErrorListener import ErrorListener

    classes = {}
    mods = []

    sys.path.insert(0, antlr_output_dir)
    with CallOnExit(lambda: sys.path.pop(0)):
        for suffix in [ "Lexer",
                        "Parser",
                        "Visitor",
                      ]:
            name = "{}{}".format(name_prefix, suffix)

            mod = importlib.import_module(name)
            assert mod

            cls = getattr(mod, name)
            assert cls

            classes[suffix] = cls
            mods.append(mod)

    # ----------------------------------------------------------------------
    class Parser(object):

        # ----------------------------------------------------------------------
        class Meta(type):
            
            # ----------------------------------------------------------------------
            def __init__(cls, *args, **kwargs):
                # Augment the Parser class with the ANTLR4 objects
                for k, v in classes.iteritems():
                    setattr(cls, k, v)

            # ----------------------------------------------------------------------
            def __getattr__(cls, name):
                # Most of the time, this will be called when referencing
                # a token by name to get its numerical value.
                return getattr(cls.Parser, name)

        # ----------------------------------------------------------------------
        
        __metaclass__                       = Meta

        # ----------------------------------------------------------------------
        @staticmethod
        def Parse( visitor,
                   s, 
                   source=None,
                 ):
            lexer = classes["Lexer"](antlr4.InputStream(s))
            tokens = antlr4.CommonTokenStream(lexer)

            tokens.fill()

            parser = classes["Parser"](tokens)
            parser.addErrorListener(ErrorListener(source or "<input>"))

            ast = parser.statements()
            assert ast

            ast.accept(visitor)

        # ----------------------------------------------------------------------
        @classmethod
        def GetLiteral(cls, value):
            return GetLiteral(cls, value)

    # ----------------------------------------------------------------------
    
    return Parser
