# ---------------------------------------------------------------------------
# |  
# |  Elements.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/07/2015 10:44:20 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import copy
import os
import sys

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)   # <Redefining build-in type> pylint: disable = W0622

from . import Exceptions

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Element(object):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  name,
                  parent,
                  source,
                  line,
                  column,
                  is_definition_only,
                  is_external,
                  additional_data,
                  pragma_data,
                ):
        self.GivenName                      = name
        self.Name                           = additional_data.get("plural", name)
        self.Parent                         = parent
        self.Source                         = source
        self.Line                           = line
        self.Column                         = column
        self.IsDefinitionOnly               = is_definition_only
        self.IsExternal                     = is_external
        self.AdditionalData                 = additional_data
        self.PragmaData                     = pragma_data
        
        # As a convenience, make all of the additional data available
        # on the object.
        for k, v in additional_data.iteritems():
            if hasattr(self, k):
                raise Exceptions.InvalidAttributeNameException( source,
                                                                line,
                                                                column,
                                                                name=k,
                                                              )

            setattr(self, k, v)

        self._dotted_name = None
        self._dotted_type_name = None

    # ---------------------------------------------------------------------------
    @property
    def DottedName(self):
        if self._dotted_name == None:
            self._dotted_name = self._DottedNameImpl(lambda e: e.Name)

        return self._dotted_name

    # ---------------------------------------------------------------------------
    @property
    def DottedTypeName(self):
        if self._dotted_type_name == None:
            self._dotted_type_name = self._DottedNameImpl(lambda e: e.GivenName)

        return self._dotted_type_name

    # ---------------------------------------------------------------------------
    def ResolveAliases(self):
        return self

    # ---------------------------------------------------------------------------
    def ResolveAll(self):
        return self

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _DottedNameImpl(self, name_functor):
        names = []

        element = self
        while element:
            names.append(name_functor(element))
            element = element.Parent

        names.reverse()

        return '.'.join(names)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class TypeInfoMixin(object):

    # ---------------------------------------------------------------------------
    def __init__(self, type_info):
        self.TypeInfo                       = type_info

# ---------------------------------------------------------------------------
class ChildrenMixin(object):

    # ---------------------------------------------------------------------------
    def __init__(self, children):
        self.Children                       = children

# ---------------------------------------------------------------------------
class ReferenceMixin(object):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  reference,
                  is_new_type,
                  original_additional_data_names,
                  original_pragma_data_names,
                ):
        self.Reference                      = reference
        self.IsNewType                      = is_new_type
        self.OriginalAdditionalDataNames    = original_additional_data_names
        self.OriginalPragmaDataNames        = original_pragma_data_names

    # ---------------------------------------------------------------------------
    def ResolveAll(self):
        return self.Reference.ResolveAll()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class FundamentalElement(TypeInfoMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  is_attribute,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        TypeInfoMixin.__init__(self, type_info)

        self.IsAttribute                    = is_attribute

# ---------------------------------------------------------------------------
class CompoundElement(TypeInfoMixin, ChildrenMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  children,
                  base,
                  derived_elements,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ChildrenMixin.__init__(self, children)
        TypeInfoMixin.__init__(self, type_info)

        self.Base                           = base
        self.DerivedElements                = derived_elements

# ---------------------------------------------------------------------------
class SimpleElement(TypeInfoMixin, ChildrenMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  children,
                  children_type_info,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ChildrenMixin.__init__(self, children)
        TypeInfoMixin.__init__(self, type_info)

        self.Attributes                     = self.Children
        self.AttributeTypeInfo              = children_type_info

# ---------------------------------------------------------------------------
class AliasElement(TypeInfoMixin, ReferenceMixin, Element):
    
    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  reference,
                  is_new_type,
                  is_attribute,
                  pragma_data,
                  *args,
                  **kwargs
                ):
        Element.__init__( self, 
                          *args, 
                          pragma_data=pragma_data,
                          **kwargs
                        )
        ReferenceMixin.__init__( self,
                                 reference,
                                 is_new_type,
                                 [],
                                 list(pragma_data.keys()),
                               )
        TypeInfoMixin.__init__(self, type_info)

        self.IsAttribute                    = is_attribute

    # ---------------------------------------------------------------------------
    def ResolveAliases(self):
        return self.Reference.ResolveAliases()

# ---------------------------------------------------------------------------
class AugmentedElement(TypeInfoMixin, ReferenceMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  reference,
                  is_new_type,
                  is_attribute,
                  was_arity_explicitly_provided,
                  additional_data,
                  pragma_data,
                  *args,
                  **kwargs
                ):
        Element.__init__( self,
                          *args,
                          additional_data=additional_data,
                          pragma_data=pragma_data,
                          **kwargs
                        )
        ReferenceMixin.__init__( self,
                                 reference,
                                 is_new_type,
                                 list(additional_data.keys()),
                                 list(pragma_data.keys()),
                               )
        TypeInfoMixin.__init__(self, type_info)

        self.IsAttribute                    = is_attribute
        self.WasArityExplicitlyProvided     = was_arity_explicitly_provided

# ---------------------------------------------------------------------------
class ExtensionElement(Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  arity,
                  positional_arguments,
                  keyword_arguments,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)

        self.Arity                          = arity
        self.PositionalArguments            = positional_arguments
        self.KeywordArguments               = keyword_arguments
