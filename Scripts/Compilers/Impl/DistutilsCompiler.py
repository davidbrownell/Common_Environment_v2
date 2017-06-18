# ----------------------------------------------------------------------
# |  
# |  DistutilsCompiler.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-06-18 15:16:41
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from six.moves import StringIO

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment.Interface import *
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.Compiler import Compiler as CompilerMod
from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
from CommonEnvironment.Compiler.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin
from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class DistutilsCompiler( AtomicInputProcessingMixin,
                         AlwaysInvocationQueryMixin,
                         CustomInvocationMixin,
                         MultipleOutputMixin,
                         CompilerMod.Compiler,
                       ):
    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    Description                             = "Creates an executable for a python file"
    Type                                    = CompilerMod.Compiler.TypeValue.File

    ( BuildType_Console,
      BuildType_Windows,
    ) = range(2)

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def IsSupported(item):
        return os.path.splitext(item)[1] in [ ".py", ]

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetRequiredContextNames(cls):
        return [ "output_dir", ] + \
               super(DistutilsCompiler, cls)._GetRequiredContextNames()

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetOptionalMetadata(cls):
        return { "build_type" : cls.BuildType_Console,
                 "include_tcl" : False,
                 "no_optimize" : False,
                 "no_bundle" : False,
                 "manifest_filename" : None,
                 "icon_filename" : None,
                 "paths" : [],
                 "includes" : [],
                 "excludes" : [],
                 "packages" : [],
                 "distutil_args" : [],
                 "output_name" : None,

                 # Embedded metadata
                 "comments" : '',
                 "company_name" : '',
                 "file_description" : '',
                 "internal_name" : '',
                 "copyright" : '',
                 "trademarks" : '',
                 "name" : '',
                 "version" : '',
               }

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        
        # Create the output_filenames
        output_filenames = []

        if len(context.input_filenames) == 1:
            output_filenames.append(os.path.join(context.output_dir, context.output_name or "{}.exe".format(os.path.splitext(os.path.basename(context.input_filenames[0]))[0])))
        else:
            if context.output_name != None:
                raise Exception("'output_name' can not be specified when multipe input files are provided")

            for input_filename in context.input_filenames:
                name = os.path.splitext(os.path.basename(input_filename))[0]

                output_filenames.append(os.path.join(context.output_dir, name, "{}.exe".format(name)))

        context.output_filenames = output_filenames
                
        # Ensure that the path of the inputs are included
        for input_filename in context.input_filenames:
            dirname = os.path.dirname(input_filename)
            if dirname not in context.paths:
                context.paths.append(dirname)

        if not context.include_tcl:
            context.excludes += [ "Tkconstants", "Tkinter", "tcl", ]
        del context.include_tcl

        return super(DistutilsCompiler, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls, 
                     invoke_reason, 
                     context, 
                     status_stream, 
                     verbose_stream,
                     verbose,
                   ):
        for index, input_filename in enumerate(context.input_filenames):
            status_stream.write("Processing '{}' ({} of {})...".format( input_filename,
                                                                        index + 1,
                                                                        len(context.input_filenames),
                                                                      ))
            with status_stream.DoneManager(associated_stream=verbose_stream) as (this_dm, this_verbose_stream):
                output_filename = context.output_filenames[index]
                
                generated_python_content = cls._GenerateScriptContent( context, 
                                                                       input_filename,
                                                                       output_filename,
                                                                     )
                assert generated_python_content

                temp_filename = Shell.GetEnvironment().CreateTempFilename(".py")
                with open(temp_filename, 'w') as f:
                    f.write(generated_python_content)

                with CallOnExit(lambda: os.remove(temp_filename)):
                    sink = StringIO()

                    this_dm.result = cls._Compile(context, temp_filename, StreamDecorator([ sink, this_verbose_stream, ]))
                    if this_dm.result != 0:
                        if not verbose:
                            this_dm.stream.write(sink.getvalue())

                    return this_dm.result

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GenerateScriptContent(context, input_filename, output_filename):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _Compile(context, script_filename, output_stream):
        raise Exception("Abstract method")
    
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def CreateCompileMethod(Compiler):
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(arity='+'),
                                      output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                      output_name=CommandLine.StringTypeInfo(arity='?'),
                                      build_type=CommandLine.EnumTypeInfo([ "console", "windows", ]),
                                      manifest_filename=CommandLine.FilenameTypeInfo(arity='?'),
                                      icon_filename=CommandLine.FilenameTypeInfo(arity='?'),
                                      path=CommandLine.DirectoryTypeInfo(arity='*'),
                                      include=CommandLine.StringTypeInfo(arity='*'),
                                      exclude=CommandLine.StringTypeInfo(arity='*'),
                                      package=CommandLine.StringTypeInfo(arity='*'),
                                      distutil_arg=CommandLine.StringTypeInfo(arity='*'),
                                      
                                      comments=CommandLine.StringTypeInfo(arity='?'),
                                      company_name=CommandLine.StringTypeInfo(arity='?'),
                                      file_description=CommandLine.StringTypeInfo(arity='?'),
                                      internal_name=CommandLine.StringTypeInfo(arity='?'),
                                      copyright=CommandLine.StringTypeInfo(arity='?'),
                                      trademarks=CommandLine.StringTypeInfo(arity='?'),
                                      name=CommandLine.StringTypeInfo(arity='?'),
                                      version=CommandLine.StringTypeInfo(arity='?'),
    
                                      output_stream=None,
                                    )
    def Compile( input,
                 output_dir,
                 output_name=None,
                 build_type="console",
                 include_tcl=False,
                 no_optimize=False,
                 no_bundle=False,
                 manifest_filename=None,
                 icon_filename=None,
                 path=None,
                 include=None,
                 exclude=None,
                 package=None,
                 distutil_arg=None,
    
                 comments=None,
                 company_name=None,
                 file_description=None,
                 internal_name=None,
                 copyright=None,
                 trademarks=None,
                 name=None,
                 version=None,
    
                 output_stream=sys.stdout,
                 verbose=False,
               ):
        if build_type == "console":
            build_type = Compiler.BuildType_Console
        elif build_type == "windows":
            build_type = Compiler.BuildType_Windows
        else:
            assert False
    
        return CompilerMod.CommandLineCompile( Compiler,
                                               input,
                                               output_stream,
                                               verbose,
    
                                               output_dir=output_dir,
                                               output_name=output_name,
                                               build_type=build_type,
                                               include_tcl=include_tcl,
                                               no_optimize=no_optimize,
                                               no_bundle=no_bundle,
                                               manifest_filename=manifest_filename,
                                               icon_filename=icon_filename,
                                               paths=path or [],
                                               includes=include or [],
                                               excludes=exclude or [],
                                               packages=package or [],
                                               distutil_args=distutil_arg or [],
    
                                               comments=comments,
                                               company_name=company_name,
                                               file_description=file_description,
                                               internal_name=internal_name,
                                               copyright=copyright,
                                               trademarks=trademarks,
                                               name=name,
                                               version=version,
                                             )
    
    # ----------------------------------------------------------------------

    return Compile

# ----------------------------------------------------------------------
def CreateCleanMethod(Compiler):
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(),
                                      output_stream=None,
                                    )
    def Clean( output_dir,
               output_stream=sys.stdout,
             ):
        return CompilerMod.CommandLineClean(output_dir, output_stream)
    
    # ----------------------------------------------------------------------

    return Clean
