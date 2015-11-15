# ---------------------------------------------------------------------------
# |  
# |  Exceptions.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/06/2015 04:07:10 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class SimpleSchemaException(Exception):
    def __init__( self,
                  source,
                  line,
                  column,
                  *args,
                  **kwargs
                ):
        if isinstance(source, (list, tuple)) and hasattr(source[-1], "filename"):
            self.Source                     = source[-1].filename
        else:
            self.Source                     = source

        self.Line                           = line
        self.Column                         = column

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        msg = "{text} ({source} [{line} <{column}>])".format( text=(args[0] if args else self.Display).format(**self.__dict__),
                                                              source=self.Source,
                                                              line=self.Line,
                                                              column=self.Column,
                                                            )

        super(SimpleSchemaException, self).__init__(msg)

# ---------------------------------------------------------------------------
class ANTLRException(SimpleSchemaException):
    def __init__(self, msg, source, line, column):
        super(ANTLRException, self).__init__( source,
                                              line,
                                              column,
                                              msg,
                                            )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class ParseUnsupportedSimpleObjects(SimpleSchemaException):                 Display = "Simple objects are not supported"
class ParseUnsupportedCustomTypes(SimpleSchemaException):                   Display = "Custom elements are not supported"
class ParseUnsupportedAttributes(SimpleSchemaException):                    Display = "Attributes are not supported"

class ParseInvalidTripleStringHeader(SimpleSchemaException):                Display = "The content in a triple quote string must begin on a line horizontally aligned with the opening set of quotes"
class ParseInvalidTripleStringFooter(SimpleSchemaException):                Display = "The content in a triple quote string must end on a line horizontally aligned  with the opening set of quotes"
class ParseInvalidTripleStringPrefix(SimpleSchemaException):                Display = "The content in a triple quote string must be horizontally aligned with the opening set of quotes"

class ParseInvalidIncludeException(SimpleSchemaException):                  Display = "The included filename '{name}' is not a valid filename"
class ParseInvalidExtensionException(SimpleSchemaException):                Display = "The extension '{name}' is not recognized"
class ParseInvalidReferenceException(SimpleSchemaException):                Display = "The reference '{name}' is not a valid reference"
class ParseInvalidStringLengthException(SimpleSchemaException):             Display = "The string length '{value}' is not a valid value"
class ParseInvalidIntegerBytesException(SimpleSchemaException):             Display = "The bytes '{value}' is not a valid value"
class ParseInvalidArityException(SimpleSchemaException):                    Display = "The arity '{value}' is not a valid value"
class ParseInvalidMaxValueException(SimpleSchemaException):                 Display = "'{value}' is not a valid value"

class ParseDuplicateConfigException(SimpleSchemaException):                 Display = "Configuration information for '{name}' has already been specified in {source} <{line} [{column}]>"
class ParseDuplicateExtensionException(SimpleSchemaException):              Display = "The extension '{name}' has already been specified in {source} <{line} [{column}]>"
class ParseDuplicateMetadataException(SimpleSchemaException):               Display = "Metadata for '{tag}' has already been specified"
class ParseDuplicateKeywordException(SimpleSchemaException):                Display = "The keyword '{keyword}' has already been specified"

class ParseMismatchedEnumValuesException(SimpleSchemaException):            Display = "The number of friendly- and standard-values must match (Num standard: {num_values}, Num friendly: {num_friendly_values})"
