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
class Arity(object):

    # ---------------------------------------------------------------------------
    def __init__(self, min, max=None):
        self.Min                            = min
        self.Max                            = max

    # ---------------------------------------------------------------------------
    def IsOptional(self):
        return self.Min == 0 and self.Max == 1

    # ---------------------------------------------------------------------------
    def IsCollection(self):
        return self.Max == None or self.Max > 1

# ---------------------------------------------------------------------------
class Element(object):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  name,
                  parent,
                  type_arity,
                  data_arity,
                  source,
                  line,
                  column,
                  is_external,
                  additional_data,
                  pragma_data,
                ):
        self.Name                           = name
        self.Parent                         = parent
        self.TypeArity                      = type_arity
        self.DataArity                      = data_arity
        self.Source                         = source
        self.Line                           = line
        self.Column                         = column
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
            self._dotted_name = self._DottedNameImpl(lambda e: getattr(e, "plural", ellipsis.Name))

        return self._dotted_name

    # ---------------------------------------------------------------------------
    @property
    def DottedTypeName(self):
        if self._dotted_type_name == None:
            self._dotted_type_name = self._DottedNameImpl(lambda e: e.Name)

        return self._dotted_type_name

    # ---------------------------------------------------------------------------
    @property
    def Arity(self):
        return self.DataArity or self.TypeArity

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
class FundamentalTypeMixin(object):

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
                  is_attribute,
                  original_additional_data_names,
                  original_pragma_data_names,
                ):
        self.Reference                      = reference
        self.IsNewType                      = is_new_type
        self.IsAttribute                    = is_attribute
        self.OriginalAdditionalDataNames    = original_additional_data_names
        self.OriginalPragmaDataNames        = original_pragma_data_names

    # ---------------------------------------------------------------------------
    def ResolveAll(self):
        return self.Reference.ResolveAll()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class FundamentalElement(FundamentalTypeMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  is_attribute,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        FundamentalTypeMixin.__init__(self, type_info)

        self.IsAttribute                    = is_attribute

# ---------------------------------------------------------------------------
class CompoundElement(ChildrenMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  children,
                  base,
                  derived_elements,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ChildrenMixin.__init__(self, children)

        self.Base                           = base
        self.DerivedElements                = derived_elements

# ---------------------------------------------------------------------------
class SimpleElement(FundamentalTypeMixin, ChildrenMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  children,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        FundamentalTypeMixin.__init__(self, type_info)
        ChildrenMixin.__init__(self, children)

        self.Attributes                     = self.Children

# ---------------------------------------------------------------------------
class AliasElement(ReferenceMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
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
                                 is_attribute,
                                 [],
                                 list(pragma_data.keys()),
                               )

    # ---------------------------------------------------------------------------
    def ResolveAliases(self):
        return self.Reference.ResolveAliases()

# ---------------------------------------------------------------------------
class AugmentedElement(ReferenceMixin, Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
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
                                 is_attribute,
                                 list(additional_data.keys()),
                                 list(pragma_data.keys()),
                               )

        self.WasArityExplicitlyProvided     = was_arity_explicitly_provided

# ---------------------------------------------------------------------------
class ExtensionElement(Element):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  positional_arguments,
                  keyword_arguments,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)

        self.PositionalArguments            = positional_arguments
        self.KeywordArguments               = keyword_arguments
