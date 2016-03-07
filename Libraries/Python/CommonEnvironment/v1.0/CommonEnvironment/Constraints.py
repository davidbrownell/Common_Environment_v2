# ---------------------------------------------------------------------------
# |  
# |  Constraints.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/27/2015 06:41:30 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inflect
import inspect
import itertools
import os
import sys

import wrapt

import TypeInfo

from TypeInfo.FundamentalTypes import *     # <Unused import> pylint: disable = W0611, W0614

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

Plural = inflect.engine()

# ---------------------------------------------------------------------------
@wrapt.decorator
class FunctionConstraint(object):

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  postcondition=None,
                  postconditions=None,
                  **precondition_validation_types
                ): 
        self.Preconditions                  = precondition_validation_types
        self.Postconditions                 = postconditions or []

        if postcondition:
            self.Postconditions.append(postcondition)

        if not self.Preconditions and not self.Postconditions:
            raise Exception("Preconditions and/or postconditions must be provided")

        self._arg_mapper                    = None

    # ---------------------------------------------------------------------------
    def __call__(self, wrapped, instance, args, kwargs):
        if self._arg_mapper == None:
            # Create a function that will map all positional arguments into the keyword map
            arg_info = inspect.getargspec(wrapped)
        
            arg_defaults = arg_info.defaults or []
            optional_args = arg_info.args[len(arg_info.args) - len(arg_defaults) :]

            if self.Preconditions:
                first_optional_arg_index = len(arg_info.args) - len(optional_args)

                # Ensure that the validation values match the function arguments
                validation_names = self.Preconditions.keys()
                missing = []
                
                for index, arg in enumerate(arg_info.args):
                    if arg in validation_names:
                        validation_names.remove(arg)
                    elif index < first_optional_arg_index:
                        missing.append(arg)
                    else:
                        default_value = arg_defaults[index - first_optional_arg_index]
                        these_kwargs = {}

                        if isinstance(default_value, str) and default_value == '':
                            these_kwargs["min_length"] = 0

                        self.Preconditions[arg] = FundamentalTypeInfo.CreateTypeInfo(type(default_value), **these_kwargs)
                
                if missing:
                    raise Exception("Preconditions for {} were not provided in {}".format( ', '.join([ "'{}'".format(arg) for arg in missing ]),
                                                                                           wrapped,
                                                                                         ))
                
                if validation_names:
                    raise Exception("The {preconditions} {pcs} {were} provided but did not match the argument names in {func}".format( preconditions=Plural.plural("precondition", len(validation_names)),
                                                                                                                                       pcs=', '.join([ "'{}'".format(validation_name) for validation_name in validation_names ]),
                                                                                                                                       were=Plural.plural_verb("was", len(validation_names)),
                                                                                                                                       func=wrapped,
                                                                                                                                     ))
                
            # ---------------------------------------------------------------------------
            def Func(args, kwargs):
                # Copy the positional args into the keyword map
                assert len(args) <= len(arg_info.args)

                index = 0
                while index < len(args):
                    kwargs[arg_info.args[index]] = args[index]
                    index += 1

                # Copy the optional args
                for arg, default_value in itertools.izip(optional_args, arg_defaults):
                    if arg not in kwargs:
                        kwargs[arg] = default_value

                        # Default parameter values in python are strange in that it is better to provide a 
                        # None value rather than an empty list when the arity is '*'. Handle that wonkiness
                        # here by providing the actual value.
                        if ( default_value == None and 
                             arg in self.Preconditions and 
                             self.Preconditions[arg] != None and 
                             self.Preconditions[arg].Arity.IsCollection
                           ):
                            kwargs[arg] = []

                return kwargs

            # ---------------------------------------------------------------------------
            
            self._arg_mapper = Func

        # Validate the arguments
        kwargs = self._arg_mapper(args, kwargs)

        if self.Preconditions:
            assert len(kwargs) == len(self.Preconditions)
            
            for k, v in kwargs.iteritems():
                assert k in self.Preconditions, k

                type_info = self.Preconditions[k]
                if type_info == None:
                    continue

                result = type_info.ValidateNoThrow(v)
                if result:
                    raise TypeInfo.ValidationException("Validation for the arg '{}' failed - {}".format(k, result))

                kwargs[k] = type_info.Postprocess(v)
                
        # Invoke the function
        result = wrapped(**kwargs)

        for postcondition in self.Postconditions:
            if postcondition == None:
                continue

            validation_result = postcondition.ValidateNoThrow(result)
            if validation_result:
                raise Exception("Validation for the result failed - {}".format(validation_result))

        return result

FunctionConstraints = FunctionConstraint
