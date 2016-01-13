# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/31/2015 06:08:53 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import copy
import inspect
import os
import re
import shutil
import sys
import textwrap

from StringIO import StringIO

from CommonEnvironment import CommandLine
from CommonEnvironment import Enum
from CommonEnvironment.FileSystem import *
from CommonEnvironment.Interface import *
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

from .InputProcessingMixin import InputProcessingMixin
from .InvocationMixin import InvocationMixin
from .InvocationQueryMixin import InvocationQueryMixin
from .OutputMixin import OutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Base( InputProcessingMixin,
            InvocationMixin,
            InvocationQueryMixin,
            OutputMixin,
          ):
    """\
    Base class for Compilers, CodeGenerators, Validators, and other compiler-like
    super classes. For simplicity, these classes are referred to as "compilers" 
    within this file.
    """

    # ---------------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ---------------------------------------------------------------------------
    TypeValue = Enum.Create( "File",        # The compiler operates on individual files (1 or more)
                             "Directory",   # The compiler operates on files within a directory
                           )

    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Type(self):
        raise Exception("Abstract property")

    @abstractproperty
    def InvokeVerb(self):
        raise Exception("Abstract property")

    # ---------------------------------------------------------------------------
    # |  One of the following values will be set to True by a super class
    IsCompiler                              = False
    IsCodeGenerator                         = False
    IsVerifier                              = False
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def ValidateEnvironment():
        """\
        Overload this method if the compiler can only run in certain environments.
        Return a string with text if the environment isn't valid.
        """
        pass

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsSupported(item):
        """\
        Returns True if the given input is supported by the compiler.
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupportedTestFile(item):
        return True
        
    # ---------------------------------------------------------------------------
    @classmethod
    def ItemNameToTestName(cls, item_name, test_name):
        """Returns the likely name of the test given the source filename."""

        if cls.Type == cls.TypeValue.Directory:
            # We can't reason about test directories, so just return the directory itself
            return item_name

        elif cls.Type == cls.TypeValue.File:            # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
            path, name = os.path.split(item_name)
            name, ext = os.path.splitext(name)

            return os.path.join(path, test_name, "{name}.{test_type}{ext}".format( name=name,
                                                                                   test_type=test_name[:-1] if test_name[-1] == 's' else test_name,
                                                                                   ext=ext,
                                                                                 ))

        else:
            assert False, (cls.Name, cls.Type)
    
    # ---------------------------------------------------------------------------
    @classmethod
    def GetSystemUnderTest(cls, test_filename):
        if cls.Type == cls.TypeValue.Directory:
            # We can't reason about test directories, so just return the directory itself
            return test_filename

        elif cls.Type == cls.TypeValue.File:            # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
            path, name = os.path.split(test_filename)

            match = re.match( r"^(?P<name>.+?)\.(?P<test_type>.+?)(?P<ext>\..+?)$",
                              name,
                            )
            assert match, name

            name = "{}{}".format(match.group("name"), match.group("ext"))
            test_type = match.group("test_type")

            if path and os.path.basename(path) == "{}{}".format(test_type, '' if test_type[-1] == 's' else 's'):
                path = os.path.dirname(path)

            return os.path.join(path, name)

        else:
            assert False, (cls.Name, cls.Type)

    # ---------------------------------------------------------------------------
    @classmethod
    def GenerateContextItems( cls,
                              inputs,
                              verbose_stream=None,
                              **kwargs
                            ):
        """\
        Yields one or more context items depending on the compiler type (file vs. directory),
        how it processes input (individual vs. atomic), and the input actually provided
        (file vs. directory).
        """

        # This method will always be called early within the invocation process, so use
        # it as a hook to ensure that we are working with fully formed objects.

        # ---------------------------------------------------------------------------
        def EnsureValid():
            classes = inspect.getmro(cls)

            # ---------------------------------------------------------------------------
            def Impl(desc, *items):
                base_count = 0

                for item in items:
                    if item in classes:
                        base_count += 1

                assert base_count == 1, (cls.Name, desc, base_count, '\n'.join([ str(c) for c in classes ]))

            # ---------------------------------------------------------------------------
            
            # CompilerType
            from CommonEnvironment.Compiler.Compiler import Compiler as CompilerClass
            from CommonEnvironment.Compiler.CodeGenerator import CodeGenerator
            from CommonEnvironment.Compiler.Verifier import Verifier

            Impl("CompilerType", CompilerClass, CodeGenerator, Verifier)

            # InputProcessingMixin
            from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
            from CommonEnvironment.Compiler.InputProcessingMixin.IndividualInputProcessingMixin import IndividualInputProcessingMixin
            
            Impl("InputProcessingMixin", AtomicInputProcessingMixin, IndividualInputProcessingMixin)

            # InvocationQueryMixin
            from CommonEnvironment.Compiler.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
            from CommonEnvironment.Compiler.InvocationQueryMixin.ConditionalInvocationQueryMixin import ConditionalInvocationQueryMixin

            Impl("InvocationQueryMixin", AlwaysInvocationQueryMixin, ConditionalInvocationQueryMixin)

            # InvocationMixin
            from CommonEnvironment.Compiler.InvocationMixin.CommandLineInvocationMixin import CommandLineInvocationMixin
            from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin

            Impl("InvocationMixin", CommandLineInvocationMixin, CustomInvocationMixin)

            # OutputMixin
            from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin
            from CommonEnvironment.Compiler.OutputMixin.NoOutputMixin import NoOutputMixin
            from CommonEnvironment.Compiler.OutputMixin.SingleOutputMixin import SingleOutputMixin

            Impl("OutputMixin", MultipleOutputMixin, NoOutputMixin, SingleOutputMixin)

        # ---------------------------------------------------------------------------
        
        EnsureValid()

        # Continue with normal processing
        verbose_stream = verbose_stream or StreamDecorator(verbose_stream)

        if not isinstance(inputs, list):
            inputs = [ inputs, ]

        invocation_group_inputs = []

        for input in inputs:
            if os.path.isfile(input):
                if cls.Type == cls.TypeValue.File:      # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                    potential_inputs = [ input, ]
                elif cls.Type == cls.TypeValue.Directory:
                    raise Exception("The filename '{}' was provided as input, but this compiler operates on directories".format(input))
                else:
                    assert False, (cls.Name, cls.Type)

            elif os.path.isdir(input):
                if cls.Type == cls.TypeValue.File:      # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                    potential_inputs = list(WalkFiles(input))
                elif cls.Type == cls.TypeValue.Directory:
                    potential_inputs = [ input, ]
                else:
                    assert False, (cls.Name, cls.Type)

            else:
                raise Exception("The input '{}' is not a valid file or directory".format(input))

            added_input = False

            for potential_input in potential_inputs:
                if cls.IsSupported(potential_input):
                    invocation_group_inputs.append(potential_input)
                    added_input = True
                else:
                    verbose_stream.write("Skipping '{}' as it is not supported by this compiler.\n".format(potential_input))

            if not added_input and os.path.isdir(input):
                verbose_stream.write("**** '{}' did not yield any inputs to process. ****\n".format(input))

        optional_metadata = cls._GetOptionalMetadata()
        
        if isinstance(optional_metadata, dict):
            # ---------------------------------------------------------------------------
            def Generator():
                for item in optional_metadata.iteritems():
                    yield item

            # ---------------------------------------------------------------------------
            
        elif isinstance(optional_metadata, list):
            # ---------------------------------------------------------------------------
            def Generator():
                for item in optional_metadata:
                    yield item

            # ---------------------------------------------------------------------------
            
        else:
            assert False, type(optional_metadata)

        for k, v in Generator():
            if k not in kwargs or kwargs[k] == None or kwargs[k] == '':
                kwargs[k] = v

        input_key = None

        for metadata in cls._CreateInvocationMetadataItems(invocation_group_inputs, copy.deepcopy(kwargs)):
            for required_name in cls._GetRequiredMetadataNames():
                if required_name not in metadata:
                    raise Exception("'{}' is required metadata".format(required_name))

            context = QuickObject(**metadata)

            if not cls._GetInputItems(context):
                continue

            display_name = cls._GetDisplayName(context)
            if display_name:
                context.display_name = display_name

            context = cls._PostprocessContextItem(context)
            if not context:
                continue

            for required_name in cls._GetRequiredContextNames():
                if not hasattr(context, required_name):
                    raise Exception("'{}' is required for {} ({})".format( required_name,
                                                                           cls.Name,
                                                                           ', '.join([ "'{}'".format(input) for input in cls._GetInputItems(context) ]),
                                                                         ))

            yield context

    # ---------------------------------------------------------------------------
    @classmethod
    def GenerateContextItem( cls,
                             inputs,
                             verbose_stream=None,
                             **kwargs
                           ):
        """\
        Convenience method when one and only one context item is expected.
        """

        contexts = list(cls.GenerateContextItems(inputs, verbose_stream, **kwargs))
        if not contexts:
            return

        if len(contexts) != 1:
            raise BaseException("Multiple contexts were found ({})".format(len(contexts)))

        return contexts[0]

    # ---------------------------------------------------------------------------
    @classmethod
    def Clean( cls,
               context,
               status_stream=sys.stdout,
               verbose_stream=None,
             ):
        """\
        Handles the complexities of cleaning, ultimately calling _CleanImpl.
        """

        assert context
        # status_stream can be None
        # verbose_stream can be None

        # The following lines ensure that we don't have to deal with the None-ness of provided streams
        status_stream = StreamDecorator(status_stream)
        verbose_stream = StreamDecorator(verbose_stream)

        this_status_stream = cls._InitializeStatusStream("Cleaning", status_stream, context)
        with status_stream.DoneManager() as stream_info:
            sink = StringIO()
            stream_info.result = cls._CleanImpl( context,
                                                 StreamDecorator([ this_status_stream, sink, ]),
                                                 StreamDecorator( sink,
                                                                  prefix='\n',
                                                                  line_prefix="  ",
                                                                ),
                                               ) or 0

            sink = "{}\n".format(sink.getvalue().rstrip())

            return stream_info.result, sink
            
    # ---------------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def _Invoke( cls,
                 context,
                 status_stream=sys.stdout,
                 verbose_stream=None,
               ):
        """\
        Handles the complexities of invocation, ultimate calling _InvokeImpl.
        """

        assert context
        # status_stream can be None
        # verbose_stream can be None

        # The following lines ensure that we don't have to deal with the None-ness of provided streams
        status_stream = StreamDecorator(status_stream)
        verbose_stream = StreamDecorator(verbose_stream)

        invoke_reason = cls._GetInvokeReason(context, verbose_stream)
        if invoke_reason == None:
            status_stream.write("No changes were detected.\n")
            return 0, "No changes were detected.\n"

        verbose_stream.flush()

        this_status_stream = cls._InitializeStatusStream(cls.InvokeVerb, status_stream, context)
        with status_stream.DoneManager() as stream_info:
            sink = StringIO()

            stream_info.result = cls._InvokeImpl( invoke_reason,
                                                  context,
                                                  StreamDecorator([ this_status_stream, sink, ]),
                                                  StreamDecorator( sink,
                                                                   prefix='\n',
                                                                   line_prefix="  ",
                                                                 ),
                                                ) or 0

            sink = "{}\n".format(sink.getvalue().rstrip())

            if stream_info.result == 0:
                cls._PersistContext(context)

            return stream_info.result, sink

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _InvokeImpl(invoke_reason, context, status_stream, output_stream):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    # |  The following methods MAY be overridden to customize behavior
    @staticmethod
    def _GetAdditionalGeneratorItems(context):
        """\
        Return a list of filenames or objects of any plugin files that participate
        in compilation. This information will be used to detect modifications that
        imply recompilation is necessary.
        """
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetDisplayName(context):
        """\
        Name used to uniquely identify the compilation in status messages.
        """
        return None
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetOptionalMetadata():
        """\
        Returns key-value pairs
        """
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetRequiredMetadataNames():
        """\
        All names that should be provided in metadata when generating context.
        """
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetRequiredContextNames():
        """\
        All names that should be provided (either by metadata or via _PostProcessContextItem)
        when generating context.
        """
        return []

    # ---------------------------------------------------------------------------
    # |  The following methods are implemented by mixins
    @staticmethod
    def _PostprocessContextItem(context):
        """\
        Returns a context object tuned specifically for the provided input.
        """
        return context
    
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @classmethod
    def _InitializeStatusStream(cls, prefix, status_stream, context):
        if hasattr(context, "display_name"):
            status_suffix = '"{}"...'.format(context.display_name)
            indentation = 4
        else:
            input_items = cls._GetInputItems(context)

            if len(input_items) == 1:
                status_suffix = '"{}"...'.format(input_items[0])
                indentation = 4
            else:
                status_suffix = "\n{}\n".format('\n'.join([ "    - {}".format(input_item) for input_item in input_items ]))
                indentation = 8

        status_stream.write("{} {}".format(prefix, status_suffix))

        return StreamDecorator( status_stream,
                                prefix='\n',
                                line_prefix=' ' * indentation,
                              )

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def CommandLineInvoke( compiler,
                       inputs,
                       output_stream,
                       verbose, 
                       **compiler_kwargs
                     ):
    # ---------------------------------------------------------------------------
    def Invoke(context, output_stream, verbose_stream):
        if compiler.IsCompiler:
            method_name = "Compile"
        elif compiler.IsCodeGenerator:
            method_name = "Generate"
        elif compiler.IsVerifier:
            method_name = "Verify"
        else:
            assert False, compiler

        return getattr(compiler, method_name)(context, output_stream, verbose_stream)

    # ---------------------------------------------------------------------------
    
    return _CommandLineImpl( compiler, 
                             inputs,
                             Invoke,
                             output_stream,
                             verbose,
                             compiler_kwargs,
                           )
    
# ---------------------------------------------------------------------------
def CommandLineClean( compiler,
                      inputs,
                      output_stream,
                      verbose,
                      **compiler_kwargs
                    ):
    return _CommandLineImpl( compiler,
                             inputs,
                             lambda context, output_stream, verbose_stream: compiler.Clean(context, output_stream),
                             output_stream,
                             verbose,
                             compiler_kwargs,
                           )

# ---------------------------------------------------------------------------
def CommandLineCleanOutputDir(output_dir, output_stream):
    if not os.path.isdir(output_dir):
        output_stream.write("'{}' does not exist.\n".format(output_dir))
        return 0

    output_stream.write("Removing '{}'...".format(output_dir))
    with StreamDecorator(output_stream).DoneManager() as stream_info:
        shutil.rmtree(output_dir)

    return stream_info.result
        
# ---------------------------------------------------------------------------
def CommandLineCleanOutputFilename(output_filename, output_stream):
    if not os.path.isfile(output_filename):
        output_stream.write("'{}' does not exist.\n".format(output_filename))
        return 0

    output_stream.write("Removing '{}'...".format(output_filename))
    with StreamDecorator(output_stream).DoneManager() as stream_info:
        os.remove(output_filename)

    return stream_info.result

# ---------------------------------------------------------------------------
def LoadFromModule(mod):
    for potential_name in [ "Compiler",
                            "CodeGenerator",
                            "Verifier",
                          ]:
        result = getattr(mod, potential_name, None)
        if result != None:
            return result

    assert False, mod

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _CommandLineImpl( compiler,
                      inputs,
                      functor,              # def Func(context, output_stream, verbose_stream) -> rval
                      output_stream,
                      verbose,
                      compiler_kwargs,
                    ):
    assert compiler
    assert inputs
    assert output_stream

    # Validate the input
    inputs = [ os.path.realpath(input) for input in inputs ]

    for input in inputs:
        if not os.path.exists(input):
            raise CommandLine.UsageException("'{}' is not a valid file or directory".format(input))

        if os.path.isfile(input):
            if compiler.Type == compiler.TypeValue.File and not compiler.IsSupported(input):
                raise CommandLine.UsageException("'{}' is not a supported file".format(input))
            elif compiler.Type == compiler.TypeValue.Directory:
                raise CommandLine.UsageException("'{}' is a file, but this compiler operates on directories".format(input))

    # Prepare the streams
    output_stream = StreamDecorator(output_stream, suffix='\n')
    
    # Execute
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix='\nExecution is ',
                                                     done_suffix='\n',
                                                     display_exceptions=False,
                                                   ) as stream_info:
        verbose_stream = StreamDecorator(stream_info.stream if verbose else None, line_prefix="INFO: ")

        stream_info.stream.write("Generating context...")
        with stream_info.stream.DoneManager():
            contexts = list(compiler.GenerateContextItems(inputs, verbose_stream, **compiler_kwargs))
            
        for index, context in enumerate(contexts):
            output_stream.flush()

            result, output = functor(context, output_stream, verbose_stream)

            stream_info.result = stream_info.result or result

            # Print the output
            heading = "Results ({result}) [{index} of {total}]".format( result=result,
                                                                        index=index + 1,
                                                                        total=len(contexts),
                                                                      )

            output = textwrap.dedent(
                """\
                
                    {heading}
                    {underline1}
               {input_items}
                        ->
               {output_items}
                    {underline2}
               {output}

                """).format( heading=heading,
                             underline1='-' * len(heading),
                             input_items='\n'.join([ "      {}".format(input_item) for input_item in compiler._GetInputItems(context) ]),               # <Access to protected method> pylint: disable = W0212
                             output_items='\n'.join([ "          {}".format(output_item) for output_item in compiler._GetOutputFilenames(context) ]),   # <Access to protected method> pylint: disable = W0212
                             underline2='=' * len(heading),
                             output=StreamDecorator.LeftJustify(output, 10, skip_first_line=False),
                           )

            if result != 0:
                output_stream.write(output)
                output_stream.flush()
            else:
                verbose_stream.write(output)
                verbose_stream.flush()
        
    return stream_info.result
