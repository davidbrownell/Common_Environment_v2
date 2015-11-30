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
class ParseUnsupportedAttributesException(SimpleSchemaException):           Display = "Attributes are not supported"
class ParseUnsupportedIncludeStatementsException(SimpleSchemaException):    Display = "Include statements are not supported"
class ParseUnsupportedConfigDeclarationsException(SimpleSchemaException):   Display = "Config declarations are not supported"

class ParseUnsupportedUnnamedDeclarationsException(SimpleSchemaException):  Display = "Unnamed declarations are not supported"
class ParseUnsupportedUnnamedObjectsException(SimpleSchemaException):       Display = "Unnamed objects are not supported"
class ParseUnsupportedNamedDeclarationsException(SimpleSchemaException):    Display = "Named declarations are not supported"
class ParseUnsupportedNamedObjectsException(SimpleSchemaException):         Display = "Named objects are not supported"

class ParseUnsupportedRootDeclarationsException(SimpleSchemaException):     Display = "Root declarations are not supported"
class ParseUnsupportedRootObjectsException(SimpleSchemaException):          Display = "Root objects are not supported"
class ParseUnsupportedChildDeclarationsException(SimpleSchemaException):    Display = "Child declarations are not supported"
class ParseUnsupportedChildObjectsException(SimpleSchemaException):         Display = "Child objects are not supported"

class ParseUnsupportedCustomTypesException(SimpleSchemaException):          Display = "Custom elements are not supported"

class ParseInvalidTripleStringHeaderException(SimpleSchemaException):       Display = "The content in a triple quote string must begin on a line horizontally aligned with the opening set of quotes"
class ParseInvalidTripleStringFooterException(SimpleSchemaException):       Display = "The content in a triple quote string must end on a line horizontally aligned  with the opening set of quotes"
class ParseInvalidTripleStringPrefixException(SimpleSchemaException):       Display = "The content in a triple quote string must be horizontally aligned with the opening set of quotes"

class ParseInvalidIncludeException(SimpleSchemaException):                  Display = "The included filename '{name}' is not a valid filename"
class ParseInvalidExtensionException(SimpleSchemaException):                Display = "The extension '{name}' is not recognized"
class ParseInvalidIntegerBytesException(SimpleSchemaException):             Display = "The bytes '{value}' is not a valid value"
class ParseInvalidArityException(SimpleSchemaException):                    Display = "The arity '{value}' is not a valid value"

class ParseDuplicateConfigException(SimpleSchemaException):                 Display = "Configuration information for '{name}' has already been specified in {source} <{line} [{column}]>"
class ParseDuplicateMetadataException(SimpleSchemaException):               Display = "Metadata for '{name}' has already been specified"
class ParseDuplicateKeywordException(SimpleSchemaException):                Display = "The keyword '{keyword}' has already been specified"

class ValidateInvalidReferenceException(SimpleSchemaException):             Display = "The reference '{name}' could not be resolved"
class ValidateCircularDependencyException(SimpleSchemaException):           Display = "A circular dependency was detected:\n{info}\n"
class ValidateUnsupportedSimpleObjectsException(SimpleSchemaException):     Display = "Simple objects are not supported"
class ValidateUnsupportedAliasesException(SimpleSchemaException):           Display = "Aliases are not supported"
class ValidateUnsupportedAugmentationsException(SimpleSchemaException):     Display = "Augmentations are not supported"

class ValidateInvalidSimpleObjectChildException(SimpleSchemaException):     Display = "Simple objects may only have attributes as children"

class ValidateDuplicateNameException(SimpleSchemaException):                Display = "The name '{name}' has already been specified in {source} <{line} [{column}]>"
class ValidateDuplicateMetadataException(SimpleSchemaException):            Display = "Metadata for '{name}' was provided multiple times"

class ValidateInvalidStringLengthException(SimpleSchemaException):          Display = "The string length '{value}' is not a valid value"
class ValidateMismatchedEnumValuesException(SimpleSchemaException):         Display = "The number of friendly- and standard-values must match (Num standard: {num_values}, Num friendly: {num_friendly_values})"
class ValidateInvalidMaxValueException(SimpleSchemaException):              Display = "'{value}' is not a valid max value"

class ValidateMetadataInvalidException(SimpleSchemaException):              Display = "The attribute '{name}' is not a supported attribute for this element type"
class ValidateMetdataRequiredException(SimpleSchemaException):              Display = "The required attribute '{name}' was not found"
class ValidateMetadataPluralNoneException(SimpleSchemaException):           Display = "The 'plural' attribute is not supported for elements with names"
class ValidateMetadataPluralSingleElementException(SimpleSchemaException):  Display = "The 'plural' attribute is only supported for elements with an arity that is greater than 1"
class ValidateMetadataDefaultException(SimpleSchemaException):              Display = "The 'default' attribute is only suppoted for optional elements"
class ValidateMetadataPolymorphicException(SimpleSchemaException):          Display = "The 'polymorphic' attribute is only supported for compound elements that are referenced by other elements"
class ValidateMetadataSuppressPolymorphicException(SimpleSchemaException):  Display = "The 'suppress_polymorphic' attribute is only supported for compound elements that reference a polymorphic compound element"
class ValidateInvalidMetadataException(SimpleSchemaException):              Display = "The attribute '{name}' is not valid: {info}"

class InvalidAttributeNameException(SimpleSchemaException):                 Display = "'{name}' cannot be used for additional_data"
