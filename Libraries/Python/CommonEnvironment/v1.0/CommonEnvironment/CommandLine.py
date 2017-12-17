# ---------------------------------------------------------------------------
# |  
# |  CommandLine.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/27/2015 10:37:57 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inspect
import os
import re
import sys
import textwrap
import types

from collections import OrderedDict

import six
import wrapt

import CommonEnvironment.Decorator
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment.StreamDecorator import StreamDecorator

# <Unused import> pylint: disable = W0611
from CommonEnvironment.Constraints import *

from CommonEnvironment import TypeInfo
from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
DEBUG_COMMAND_LINE_ARG                      = "_debug_command_line"
PROFILE_COMMAND_LINE_ARG                    = "__profile__"

MAX_COLUMN_WIDTH                            = 100

# The following are optional methods that can be defined in modules to
# override default behaviors.
CUSTOMIZATION_METHODS                       = [ "CommandLineScriptName",
                                                "CommandLineScriptDescription",
                                                "CommandLinePrefix",
                                                "CommandLineSuffix",
                                              ]

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
@wrapt.decorator
class EntryPoint(object):

    ArgumentInfo                            = NamedTuple( "ArgumentInfo", 
                                                          OrderedDict([ ( "description", '' ),
                                                                        ( "postprocess_func", None ),
                                                                        ( "allow_duplicates", False ),
                                                                        ( "ignore", False ),
                                                                      ])
                                                        )

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  _name=None,               # Prefixed with an underscore so it doesn't conflict with potential argument names
                  **args
                ):
        self.NameOverride                   = _name
        self.Args                           = args

    # ---------------------------------------------------------------------------
    def __call__(self, wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

# ---------------------------------------------------------------------------
class EntryPointData(object):

    ParamInfo                               = NamedTuple( "ParamInfo",
                                                          "type_info",
                                                          "name",
                                                          "description",
                                                          "display_arity",
                                                          "postprocess_func",
                                                          "allow_duplicates",
                                                          "is_positional",
                                                          "is_required",
                                                          "is_switch",
                                                          "default_value",
                                                        )

    # ---------------------------------------------------------------------------
    @classmethod
    def FromFunction(cls, function):
        entry_point_decorator = None
        constraint_decorator = None

        for decorator in CommonEnvironment.Decorator.EnumDecorators(function):
            # wrapt.decorator confuses standard type lookup mechanisms
            # <Use isinstance instead of type> pylint: disable = W1504

            if type(decorator) == EntryPoint:
                assert entry_point_decorator == None, function
                entry_point_decorator = decorator

            elif type(decorator) == FunctionConstraint:
                assert constraint_decorator == None, function
                constraint_decorator = decorator

        if entry_point_decorator:
            arg_spec = inspect.getargspec(function)

            if (not constraint_decorator or not constraint_decorator.Preconditions) and len(arg_spec.args) != len(arg_spec.defaults or []):
                raise Exception("'{}' must be associated with a FunctionConstraint decorator with preconditions".format(function.__name__))

            return cls(function, entry_point_decorator, constraint_decorator)

    # ---------------------------------------------------------------------------
    @classmethod
    def FromModule(cls, mod):
        entry_points = []

        for item_name in dir(mod):
            item = getattr(mod, item_name)

            epd = cls.FromFunction(item)
            if epd:
                entry_points.append(epd)

        # Sort by line number, as we want the functions displayed in the order in which they were declared
        entry_points.sort(key=lambda x: six.get_function_code(x.Func).co_firstlineno)

        return entry_points

    # ---------------------------------------------------------------------------
    def __init__( self,
                  func,
                  entry_point_decorator,
                  constraints_decorator,
                ):
        self.Func                       = func
        self.EntryPointDecorator        = entry_point_decorator
        self.ConstraintsDecorator       = constraints_decorator
        self.Name                       = self.EntryPointDecorator.NameOverride or func.__name__
        self.Description                = func.__doc__ or ''
        self.Params                     = []

        # Get the original arguments
        arg_info = inspect.getargspec(func)
    
        args = arg_info.args
        defaults = list(arg_info.defaults or [])

        first_optional_arg_index = len(args) - len(defaults)

        # Remove any explicitly ignored parameters and verify that all items
        # are accounted for.
        entry_point_decorator_names = list(six.iterkeys(self.EntryPointDecorator.Args))
        new_args = []

        for index, arg in enumerate(args):
            if arg in entry_point_decorator_names:
                entry_point_decorator_names.remove(arg)

            if ( (self.ConstraintsDecorator and arg in self.ConstraintsDecorator.Preconditions and self.ConstraintsDecorator.Preconditions[arg] == None) or
                 (arg in self.EntryPointDecorator.Args and ( entry_point_decorator.Args[arg] == None or 
                                                             entry_point_decorator.Args[arg].ignore
                                                           ))
               ):
                if index < first_optional_arg_index:
                    raise Exception("'{}' was explicitly ignored but does not have a default python value".format(arg))

                # This arg will not be included in the list of args - remove the default value
                defaults.remove(defaults[index - first_optional_arg_index])

            else:
                new_args.append(arg)

        if entry_point_decorator_names:
            raise Exception("Information was provided for arguments that don't correspond to those found in '{name}' ({args})".format( args=', '.join([ "'{}'".format(entry_point_decorator_name) for entry_point_decorator_name in entry_point_decorator_names ]),
                                                                                                                                       name=func.__name__,
                                                                                                                                     ))
        args = new_args
        first_optional_arg_index = len(args) - len(defaults)

        # Populate the args information
        is_positional = True
        
        for index, name in enumerate(args):
            if not self.ConstraintsDecorator or (name not in self.ConstraintsDecorator.Preconditions and index >= first_optional_arg_index):
                type_info = CreateTypeInfo(type(defaults[index - first_optional_arg_index]), arity='?')
            else:
                assert name in self.ConstraintsDecorator.Preconditions, (self.Name, name)
                type_info = self.ConstraintsDecorator.Preconditions[name]

            assert type_info, name
            
            if not isinstance(type_info, FUNDAMENTAL_TYPES + (DictTypeInfo, AnyOfTypeInfo)):
                raise Exception("Only fundamental types are supported ({})".format(name))

            if name in self.EntryPointDecorator.Args:
                provided_argument_info = self.EntryPointDecorator.Args[name]
                assert provided_argument_info and not provided_argument_info.ignore
            else:
                provided_argument_info = EntryPoint.ArgumentInfo()

            # Calculate the display arity
            if isinstance(type_info, DictTypeInfo):
                if not type_info.Arity.IsSingle and not type_info.Arity.IsOptional:
                    raise Exception("Dictionaries must have an arity of 1 or ? ({})".format(name))

                # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                for k, v in six.iteritems(type_info.Items):
                    if not isinstance(v, StringTypeInfo):
                        raise Exception("Dictionary value types must be strings ({}, {})".format(name, k))

                display_arity = '*' if type_info.Arity.IsOptional or not is_positional else '+'

            elif type_info.Arity.IsSingle:
                display_arity = '1'            
            elif type_info.Arity.IsOptional:
                display_arity = '?'
            elif type_info.Arity.IsCollection:
                display_arity = '*' if type_info.Arity.Min == 0 else '+'
            else:
                raise Exception("Types must have an arity of '1', '?', '+', or '*'")

            assert display_arity in [ '1', '?', '+', '*', ], display_arity
            
            # Update positional information
            if ( is_positional and 
                 (index >= first_optional_arg_index or display_arity != '1') and
                 index != len(args) - 1
               ):
                is_positional = False

            # Add the argument information
            self.Params.append(self.ParamInfo( type_info,
                                               name,
                                               provided_argument_info.description,
                                               display_arity,
                                               provided_argument_info.postprocess_func,
                                               provided_argument_info.allow_duplicates,
                                               is_positional,
                                               index < first_optional_arg_index,
                                               isinstance(type_info, BoolTypeInfo) and index >= first_optional_arg_index and defaults[index - first_optional_arg_index] != None,
                                               defaults[index - first_optional_arg_index] if index >= first_optional_arg_index else None,
                                             ))
        
    # ---------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        return self.Func(*args, **kwargs)

# ---------------------------------------------------------------------------
# <Too many instance attributes> pylint: disable = R0902
class Executor(object):

    # ---------------------------------------------------------------------------
    # <Dangerous default value> pylint: disable = W0102
    def __init__( self,
                  args=sys.argv,
                  command_line_arg_prefix='/',
                  command_line_keyword_separator='=',
                  command_line_dict_tag_value_separator=':',
                  args_in_a_file_prefix='@',
                  script_name=None,
                  script_description=None,
                  script_description_prefix=None,
                  script_description_suffix=None,
                  entry_points=None,
                ):
        mod = sys.modules["__main__"]
        
        self.Args                                       = args
        self.CommandLineArgPrefix                       = command_line_arg_prefix
        self.CommandLineKeywordSeparator                = command_line_keyword_separator
        self.CommandLineDictTagValueSeparator           = command_line_dict_tag_value_separator
        self.ArgsInAFilePrefix                          = args_in_a_file_prefix
        self.ScriptName                                 = script_name or (mod.CommandLineScriptName() if hasattr(mod, "CommandLineScriptName") else os.path.basename(self.Args[0]))
        self.ScriptDescription                          = script_description or (mod.CommandLineScriptDescription() if hasattr(mod, "CommandLineScriptDescription") else mod.__doc__) or ''
        self.ScriptDescriptionPrefix                    = script_description_prefix or (mod.CommandLinePrefix() if hasattr(mod, "CommandLinePrefix") else '')
        self.ScriptDescriptionSuffix                    = script_description_suffix or (mod.CommandLineSuffix() if hasattr(mod, "CommandLineSuffix") else '')

        self.EntryPoints                                = entry_points or EntryPointData.FromModule(mod)
        
        self._keyword_regex                             = re.compile(r"^{prefix}(?P<tag>\S+?)(?:\s*{separator}\s*(?P<value>.+)\s*)?$".format( prefix=re.escape(self.CommandLineArgPrefix),
                                                                                                                                              separator=re.escape(self.CommandLineKeywordSeparator),
                                                                                                                                            ))
        self._dict_regex                                = re.compile(r"^(?P<tag>.+?)(?<!\\){sep}(?P<value>.+)$".format( sep=re.escape(self.CommandLineDictTagValueSeparator),
                                                                                                                      ))

    # ---------------------------------------------------------------------------
    # <Too many return statements> pylint: disable = R0911
    # <Too many branches> pylint: disable = R0912
    # <Too many local variables> pylint: disable = R0914
    def Invoke( self,
                output_stream=sys.stdout,
                verbose=False,
                print_results=False,
                allow_exceptions=False,
              ):
        arg_strings = list(self.Args)

        debug_mode = False
        if len(arg_strings) > 1 and arg_strings[1].lower() == DEBUG_COMMAND_LINE_ARG:
            debug_mode = True
            del arg_strings[1]

        profile_mode = False
        if len(arg_strings) > 1 and arg_strings[1].lower() == PROFILE_COMMAND_LINE_ARG:
            profile_mode = True
            del arg_strings[1]

        # Are we looking for a request for verbose help
        if any(arg.startswith(self.CommandLineArgPrefix) and arg[len(self.CommandLineArgPrefix):].lower() in [ "?", "help", "h", ] for arg in arg_strings):
            return self.Usage(verbose=True)

        # Get the function to call
        if len(self.EntryPoints) == 1:
            # If there is only 1 entry point, don't make the user provide the
            # name on the command line.
            entry_point = self.EntryPoints[0]
            arg_strings = arg_strings[1:]
        else:
            # The first arg is the entry point name
            if len(arg_strings) < 2:
                return self.Usage()

            name = arg_strings[1]
            name_lower = name.lower()

            arg_strings = arg_strings[2:]

            entry_point = next((ep for ep in self.EntryPoints if ep.Name.lower() == name_lower), None)
            if entry_point == None:
                return self.Usage(error="'{}' is not a valid command name".format(name))

        assert entry_point

        if debug_mode:
            output_stream.write("{}\n".format('\n'.join([ str(a) for a in entry_point.Params ])))
            return 0

        # Read the arguments from a file if necessary
        if len(arg_strings) == 1 and arg_strings[0].startswith(self.ArgsInAFilePrefix):
            filename = os.path.join(os.getcwd(), arg_strings[0][len(self.ArgsInAFilePrefix):])

            if not os.path.isfile(filename):
                return self.Usage(error="'{}' is not a valid filename".format(filename))

            with open(filename) as f:
                arg_strings = [ line.strip() for line in f.read().split('\n') if line.strip() ]

        result = self._ParseCommandLine(entry_point, arg_strings)
        if isinstance(result, str):
            return self.Usage(error=result)

        kwargs = result

        if verbose:
            output_stream.write(textwrap.dedent(
                """\

                INFO: Calling '{name}' with the arguments:
                    {args}

                """).format( name=entry_point.Name,
                             args='\n'.join([ "    {k:<20} {v}".format(k="{}:".format(k), v=v) for k, v in six.iteritems(kwargs) ]),
                           ))

        # ----------------------------------------------------------------------
        def Impl():
            try:
                result = entry_point(*[], **kwargs)

                if print_results:
                    if isinstance(result, types.GeneratorType):
                        result = '\n'.join([ "{}) {}".format(index, str(item)) for index, item in enumerate(result) ])

                    output_stream.write(textwrap.dedent(
                        """\
                        ** Result **
                        {}
                        """).format(result))

                    result = 0

                if result == None:
                    result = 0

            except UsageException as ex:
                result = self.Usage(error=str(ex))
            except TypeInfo.ValidationException as ex:
                result = self.Usage(error=str(ex))
            except KeyboardInterrupt:
                result = -1
            except:
                if allow_exceptions:
                    raise
                 
                if not getattr(sys.exc_info()[1], "_DisplayedException", False):   
                    import traceback

                    output_stream.write("ERROR: {}".format(StreamDecorator.LeftJustify(traceback.format_exc(), len("ERROR: "))))
                
                result = -1

            return result

        # ----------------------------------------------------------------------
        
        # Standard mode
        if not profile_mode:
            return Impl()

        # Profile mode
        from cProfile import Profile
        from pstats import Stats

        profile = Profile()

        profile.enable()
        try:
            result = Impl()
        finally:
            profile.disable()

        Stats(profile, stream=output_stream).sort_stats("tottime").print_stats()
        return result


    # ---------------------------------------------------------------------------
    def Usage( self,
               error=None,
               error_stream=sys.stderr,
               verbose=False,
             ):
        if len(self.EntryPoints) == 1:
            standard, verbose_desc = self._GenerateUsageInformation(self.EntryPoints[0])
            if verbose:
                standard = "{}\n\n{}".format(standard, verbose_desc)

            output = "        {} {}".format(self.ScriptName, standard)
        else:
            # ---------------------------------------------------------------------------
            def FormatInlineFuncDesc(content):
                initial_whitespace = 37

                assert MAX_COLUMN_WIDTH > initial_whitespace
                content = StreamDecorator.Wrap(content, MAX_COLUMN_WIDTH - initial_whitespace)

                return StreamDecorator.LeftJustify(content, initial_whitespace)

            # ---------------------------------------------------------------------------
            
            output = [ textwrap.dedent(
                """\
                        {script_name} <command> [args]

                Where <command> can be one of the following:
                --------------------------------------------
                {commands}

                """).format( script_name=self.ScriptName,
                             commands='\n'.join([ "    - {name:<30} {desc}".format( name=ep.Name,
                                                                                    desc=FormatInlineFuncDesc(ep.Description),
                                                                                  )
                                                  for ep in self.EntryPoints
                                                ]),
                           ),
                     ]

            for ep in self.EntryPoints:
                intro = "When <command> is '{}':".format(ep.Name)

                standard, verbose_desc = self._GenerateUsageInformation(ep)

                # Insert the function name as an argument
                if '\n' in standard:
                    multi_line_args = True
                    standard = "        {}{}".format(ep.Name, StreamDecorator.LeftJustify(standard, 4))
                else:
                    multi_line_args = False
                    standard = "{} {}".format(ep.Name, standard)

                if verbose:
                    standard = "{}\n\n{}".format( standard,
                                                  StreamDecorator.LeftJustify(verbose_desc, 4, skip_first_line=False),
                                                )

                output.append(textwrap.dedent(
                    """\
                    {intro}
                    {sep}
                        {script_name}{newline}{standard}

                    """).format( intro=intro,
                                 sep='-' * len(intro),
                                 script_name=self.ScriptName,
                                 newline='\n' if multi_line_args else ' ',
                                 standard=standard,
                               ))

            output = '\n'.join(output).rstrip()

        error_stream.write(textwrap.dedent(
            """\
            {desc}{prefix}

                Usage:
            {output}

            {suffix}{additional_info}
            """).format( desc=StreamDecorator.Wrap(self.ScriptDescription, MAX_COLUMN_WIDTH),
                         prefix='' if not self.ScriptDescriptionPrefix else "\n\n{}".format(self.ScriptDescriptionPrefix),
                         output=StreamDecorator.LeftJustify(output, 4),
                         suffix='' if not self.ScriptDescriptionSuffix else "\n{}".format(self.ScriptDescriptionSuffix),
                         additional_info='' if verbose else '\n\n    Run "{script_name} {prefix}?" for additional information.\n\n'.format( script_name=self.ScriptName,
                                                                                                                                            prefix=self.CommandLineArgPrefix,
                                                                                                                                          ),
                       ))

        if error:
            error = "\n\nERROR: {}\n".format(StreamDecorator.LeftJustify(error, len("ERROR: ")))

            try:
                import colorama

                colorama.init(autoreset=True)
                error_stream = sys.stderr

                # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                error_stream.write("{}{}{}".format( colorama.Fore.RED,
                                                    colorama.Style.BRIGHT,
                                                    error,
                                                  ))
            except ImportError:
                error_stream.write(error)

        return -1

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    def _ParseCommandLine(self, entry_point, args):
        
        argument_values = {}

        # ---------------------------------------------------------------------------
        def ApplyImpl(param, arg):
            if isinstance(param.type_info, DictTypeInfo):
                # Add the dictionary values; we will validate later
                match = self._dict_regex.match(arg)
                if not match:
                    return "'{}' is not a valid dictionary entry".format(arg)

                tag = match.group("tag")
                tag = tag.replace("\\{}".format(self.CommandLineDictTagValueSeparator), self.CommandLineDictTagValueSeparator)

                value = match.group("value")

                argument_values.setdefault(param.name, OrderedDict())

                if tag not in argument_values[param.name]:
                    if param.allow_duplicates:
                        argument_values[param.name][tag] = [ value, ]
                    else:
                        argument_values[param.name][tag] = value
                else:
                    if not param.allow_duplicates:
                        return "A value for '{}'s tag '{}' has already been provided ({})".format( param.name,
                                                                                                   tag,
                                                                                                   argument_values[param.name][tag],
                                                                                                 )

                    argument_values[param.name][tag].append(value)

                return

            if param.is_switch:
                arg = StringSerialization.SerializeItem(param.type_info, not param.default_value)

            try:
                if isinstance(param.type_info, FUNDAMENTAL_TYPES):
                    value = StringSerialization.DeserializeItem(param.type_info, arg)
                elif isinstance(param.type_info, AnyOfTypeInfo):
                    found = False

                    for eti in param.type_info.ElementTypeInfos:
                        try:
                            value = StringSerialization.DeserializeItem(eti, arg)
                            found = True
                            break
                        except TypeInfo.ValidationException:
                            pass

                    if not found:
                        value = arg

                else:
                    value = arg

                if param.postprocess_func:
                    value = param.postprocess_func(value)

            except TypeInfo.ValidationException as ex:
                return str(ex)

            if param.display_arity in [ '?', '1' ,]:
                if param.name in argument_values:
                    return "A value for '{}' has already been provided ({})".format( param.name,
                                                                                     argument_values[param.name],
                                                                                   )

                argument_values[param.name] = value

            elif param.display_arity in [ '*', '+', ]:
                argument_values.setdefault(param.name, []).append(value)

            else:
                assert False
            
        # ---------------------------------------------------------------------------
        def ApplyPositionalArgument(param, arg):
            if param.is_switch:
                if ( not arg.startswith(self.CommandLineArgPrefix) or
                     arg[len(self.CommandLineArgPrefix):].lower() != param.name.lower()
                   ):
                    return "'{}' is not a recognized command line argument".format(arg)
                
                return ApplyImpl(param, None)

            return ApplyImpl(param, arg)

        # ---------------------------------------------------------------------------
        def ApplyKeywordArgument(param, arg):
            match = self._keyword_regex.match(arg)
            if not match:
                return "'{}' is not a valid keyword argument".format(arg)

            tag = match.group("tag")
            value = match.group("value")
            
            tag_lower = tag.lower()

            param = None
            for potential_param in entry_point.Params:
                if potential_param.name.lower() == tag_lower and not potential_param.is_positional:
                    param = potential_param
                    break

            if param is None:
                return "'{}' is not a recognized command line argument".format(tag)
            if value is None and not param.is_switch:
                return "A value was expected with the keyword argument '{}'".format(tag)

            return ApplyImpl(param, value)

        # ---------------------------------------------------------------------------
        
        arg_index = 0
        param_index = 0

        while param_index != len(entry_point.Params) and arg_index != len(args):
            param = entry_point.Params[param_index]
            arg = args[arg_index]
            
            if param.is_positional:
                result = ApplyPositionalArgument(param, arg)
            else:
                result = ApplyKeywordArgument(param, arg)
            
            if isinstance(result, str):
                return result

            arg_index += 1

            if param.display_arity == '1':
                param_index += 1

        # We have problems if there are still args to be populated
        if arg_index != len(args):
            return "Too many arguments were provided"

        # Ensure tha all required arguments are present
        for param in entry_point.Params:
            if param.is_required and param.name not in argument_values:
                return "'{}' is a required argument".format(param.name)

            if isinstance(param.type_info, DictTypeInfo):
                if param.name in argument_values:
                    result = param.type_info.ValidateNoThrow(argument_values[param.name])
                    if result != None:
                        return "'{}' is not in a valid state - {}".format(param.name, result)

                many_default_value = {}
            else:
                many_default_value = []

            # In theory, this will never trigger because we are ensuring arity through argument
            # positionality. However, better safe than sorry.
            result = param.type_info.ValidateArityNoThrow(argument_values.get(param.name, many_default_value if param.display_arity in [ '*', '+', ] else 0))
            if result != None:
                return "'{}' is not in a valid state - {} [unexpected]".format(param.name, result)

        return argument_values
    
    # ---------------------------------------------------------------------------
    def _GenerateUsageInformation(self, entry_point):
        verbose_cols = [ 30, 15, 8, 20, 80, ]
        verbose_template = "{name:<%d}  {type:<%d}  {arity:<%d}  {default:<%d}  {desc:<%d}" % tuple(verbose_cols)

        verbose_desc_offset = 0
        for col in verbose_cols[:-1]:
            verbose_desc_offset += col + 1

        command_line = []
        verbose = []

        if entry_point.Params:
            verbose.append(verbose_template.format( name="Name",
                                                    type="Type",
                                                    arity="Arity",
                                                    default="Default Value",
                                                    desc="Description",
                                                  ))
            verbose.append(verbose_template.format( name='-' * verbose_cols[0],
                                                    type='-' * verbose_cols[1],
                                                    arity='-' * verbose_cols[2],
                                                    default='-' * verbose_cols[3],
                                                    desc='-' * verbose_cols[4],
                                                  ))

            is_multi_line_command_line = len(entry_point.Params) > 4

            for index, param in enumerate(entry_point.Params):
                arg = param.name

                if param.is_switch:
                    arg = "{}{}".format( self.CommandLineArgPrefix,
                                         arg,
                                       )

                elif isinstance(param.type_info, DictTypeInfo):
                    if not param.is_positional:
                        prefix = "{}{}{}".format( self.CommandLineArgPrefix,
                                                  arg,
                                                  self.CommandLineKeywordSeparator,
                                                )
                    else:
                        prefix = ''

                    arg = "{}<tag>{}<value>".format( prefix,
                                                     self.CommandLineDictTagValueSeparator,
                                                   )

                elif not param.is_positional:
                    arg = "{}{}{}<value>".format( self.CommandLineArgPrefix,
                                                  arg,
                                                  self.CommandLineKeywordSeparator,
                                                )

                if param.is_required:
                    arg = "<{}>".format(arg)
                else:
                    arg = "[{}]".format(arg)

                if param.display_arity in [ '*', '+', ]:
                    arg += param.display_arity

                if is_multi_line_command_line:
                    arg = "\n    {}".format(arg)
                elif index:
                    arg = " {}".format(arg)

                command_line.append(arg)

                # Verbose
                if param.default_value != None:
                    if param.is_switch:
                        default_value = "on" if param.default_value else "off"
                    else:
                        default_value = param.default_value
                else:
                    default_value = ''

                verbose.append(verbose_template.format( name=param.name,
                                                        type="switch" if param.is_switch else "Dictionary" if isinstance(param.type_info, DictTypeInfo) else param.type_info.Desc,
                                                        arity=param.display_arity,
                                                        default=default_value,
                                                        desc=StreamDecorator.LeftJustify( '\n'.join(textwrap.wrap(param.description, 100)),
                                                                                          verbose_desc_offset + 4,
                                                                                        ),
                                                      ))

                constraints = param.type_info.ConstraintsDesc
                if constraints:
                    verbose.append("        - {}\n".format(constraints))

        return ''.join(command_line), '\n'.join(verbose)

# ---------------------------------------------------------------------------
class UsageException(Exception):
    def __init__(self, *args, **kwargs):
        super(UsageException, self).__init__(*args, **kwargs)

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def Main( allow_exceptions=False,
          *executor_args,
          **executor_kwargs
        ):
    return Executor( *executor_args,
                     **executor_kwargs
                   ).Invoke( allow_exceptions=allow_exceptions,
                           )

# ---------------------------------------------------------------------------
def DisplayOutput( result_code,
                   result,
                   display_none=True,
                   output_stream=sys.stdout,
                 ):
    output_stream.write("Result Code:       {}\n".format(result_code))
    output_stream.write("Result:            ")

    is_list = False

    if isinstance(result, (list, types.GeneratorType)):
        if not isinstance(result, list):
            result = list(result)

        is_list = True
        result = "Items ({})\n\n{}".format( len(result),
                                            '\n'.join([ str(r) for r in result ]),
                                          )
    elif result == None:
        result = str(result) if display_none else ''
    else:
        result = str(result)

    if is_list:
        output_stream.write(result)
    elif len(result.split('\n')) <= 3:
        output_stream.write(StreamDecorator.LeftJustify(result, 19))
    else:
        output_stream.write("\n{}".format(result))

    output_stream.write("\n")
    output_stream.flush()

    return result_code
