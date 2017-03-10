# ---------------------------------------------------------------------------
# |  
# |  Py2ExeCompiler.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  01/11/2016 05:25:18 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Py2Exe compiler
"""

import os
import subprocess
import shutil
import sys
import textwrap

from collections import OrderedDict
from StringIO import StringIO

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.Compiler import Compiler as CompilerMod
from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
from CommonEnvironment.Compiler.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin
from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived
class Compiler( AtomicInputProcessingMixin,
                AlwaysInvocationQueryMixin,
                CustomInvocationMixin,
                MultipleOutputMixin,
                CompilerMod.Compiler,
              ):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "Py2ExeCompiler"
    Description                             = "Creates an executable for a python file"
    Type                                    = CompilerMod.Compiler.TypeValue.File       # <Class 'Foo' has no 'Bar' member> pylint: disable = E1101, E1103

    ( BuildType_Console, 
      BuildType_Windows,
    ) = range(2)

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def ValidateEnvironment():
        if Shell.GetEnvironment().Name != "Windows":
            return "This compiler may only be invoked in the Windows environment."

    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupported(item):
        return os.path.splitext(item)[1] in [ ".py", ]

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetRequiredContextNames(cls):
        return [ "output_dir", ] + \
               super(Compiler, cls)._GetRequiredContextNames()

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

        return super(Compiler, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls, 
                     invoke_reason, 
                     context, 
                     status_stream, 
                     verbose_stream,
                     verbose,
                   ):
        # ---------------------------------------------------------------------------
        def BuildTypeToString(build_type):
            if build_type == cls.BuildType_Console:
                return "console"
            elif build_type == cls.BuildType_Windows:
                return "windows"
            else:
                assert False

        # ---------------------------------------------------------------------------

        version_info = OrderedDict()
        
        for attribute_name in [ "comments",
                                "company_name",
                                "file_description",
                                "internal_name",
                                "copyright",
                                "trademarks",
                                "name",
                                "version",
                              ]:
            value = getattr(context, attribute_name)
            if not value:
                continue
            
            version_info[attribute_name] = value
             
        for index, input_filename in enumerate(context.input_filenames):
            status_stream.write("Processing '{}' ({} of {})...".format( input_filename,
                                                                        index + 1,
                                                                        len(context.input_filenames),
                                                                      ))
            with status_stream.DoneManager(associated_stream=verbose_stream) as (this_dm, this_verbose_stream):
                output_filename = context.output_filenames[index]
                
                generated_python_content = textwrap.dedent(
                    '''\
                    import os
                    import sys
                    import textwrap

                    # win32com workaround
                    try:
                        try: import py2exe.mf as modulefinder
                        except ImportError: import modulefinder

                        import win32com

                        for p in win32com.__path__[1:]:
                            modulefinder.AddPackagePath("win32com", p)

                        for extra in [ "win32com.shell", ]:
                            __import__(extra)

                            m = sys.modules[extra]

                            for p in m.__path__[1:]:
                                modulefinder.AddPackagePath(extra, p)

                    except ImportError:
                        pass

                    import py2exe
                    from distutils.core import setup

                    {paths}
                    
                    manifest = textwrap.dedent(
                        """\\
                        {manifest}
                        """)

                    setup( name="{name}",
                           options={{ "py2exe" : {{ "optimize" : {optimize},
                                                  "bundle_files" : {bundle},
                                                  "dll_excludes" : [ "MSVCP90.dll", "mswsock.dll", "powrprof.dll", "mpr.dll", ],
                                                  "packages" : [ {packages} ],
                                                  {optional_include_statement}
                                                  {optional_exclude_statement}
                                                }},
                                   }},
                            zipfile=None,
                            {type}= [ {{ "script" : r"{script}",
                                        "dest_base" : "{name}",
                                        # "other_resources" : [ (24, 1, manifest), ],
                                        {version_info}
                                        {icon}
                                      }},
                                    ],
                         )
                    ''').format( paths='\n'.join([ 'sys.path.append(r"{}")'.format(os.path.abspath(path)) for path in context.paths ]),
                                 manifest=StreamDecorator.LeftJustify( open(context.manifest_filename).read() if context.manifest_filename != None and os.path.isfile(context.manifest_filename) else textwrap.dedent(
                                                                                """\
                                                                                <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                                                                <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0" />
                                                                                """).rstrip(),
                                                                       4,
                                                                     ),
                                 name=os.path.splitext(os.path.basename(output_filename))[0],
                                 optimize="0" if context.no_optimize else "2",
                                 bundle="3" if context.no_bundle else "1",
                                 optional_include_statement='' if not context.includes else '"includes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(include) for include in context.includes ])),
                                 optional_exclude_statement='' if not context.excludes else '"excludes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(exclude) for exclude in context.excludes ])),
                                 packages=', '.join([ '"{}"'.format(package) for package in context.packages ]),
                                 script=input_filename,
                                 type=BuildTypeToString(context.build_type),
                                 version_info='' if not version_info else StreamDecorator.LeftJustify( '\n'.join([ '"{}" : "{}",'.format(k, v) for k, v in version_info.iteritems() ]),
                                                                                                       len("setup( "),
                                                                                                     ),
                                 icon='' if context.icon_filename == None else '"icon_resources" : [ (1, "{}"), ],'.format(context.icon_filename),

                               )
                
                temp_filename = Shell.GetEnvironment().CreateTempFilename(".py")
                with open(temp_filename, 'w') as f:
                    f.write(generated_python_content)

                with CallOnExit(lambda: os.remove(temp_filename)):
                    command_line = 'python "{}" py2exe{}'.format( temp_filename,
                                                                  '' if not context.distutil_args else " {}".format(' '.join([ '"{}"'.format(arg) for arg in context.distutil_args ])),
                                                                )

                    result = subprocess.Popen( command_line,
                                               shell=True,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT,
                                             )
                                        
                    sink = StringIO()
                    output_stream = StreamDecorator([ sink, this_verbose_stream, ])
                         
                    while True:
                        line = result.stdout.readline()
                        if not line:
                            break
                            
                        output_stream.write(line)
                        
                    this_dm.result = result.wait() or 0
                    if this_dm.result != 0:
                        if not verbose:
                            this_dm.stream.write(sink.getvalue())

                        return this_dm.result

                    # Cleanup the output
                    FileSystem.RemoveTree("build")
                    
                    if os.path.isdir("dist"):
                        output_dir = os.path.dirname(output_filename)

                        FileSystem.RemoveTree(output_dir)
                        
                        shutil.move("dist", output_dir)

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
# <Too many arguments> pylint: disable = R0913
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

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(),
                                  output_stream=None,
                                )
def Clean( output_dir,
           output_stream=sys.stdout,
         ):
    return CompilerMod.CommandLineClean(output_dir, output_stream)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
