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
# |  Copyright David Brownell 2016-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Py2Exe compiler
"""

import os
import shutil
import sys
import textwrap

from collections import OrderedDict
import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Process
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Impl"))
with CallOnExit(lambda: sys.path.pop(0)):
    from DistutilsCompiler import ( CreateCompileMethod,
                                    CreateCleanMethod,
                                    DistutilsCompiler as CompilerBase,
                                  )

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived
class Compiler(CompilerBase):
    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Py2ExeCompiler"
    
    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def ValidateEnvironment():
        if Shell.GetEnvironment().Name != "Windows":
            return "This compiler may only be invoked in the Windows environment."

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _GenerateScriptContent(cls, context):
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
        
        if version_info:
            version_info = StreamDecorator.LeftJustify( '\n'.join([ '"{}" : "{}",'.format(k, v) for k, v in six.iteritems(version_info) ]),
                                                        len("setup( "),
                                                      )
        else:
            version_info = "# No version info"

        icon_statement = "# No icon" if not context.icon_filename else '"icon_resources" : [ (1, "{}"), ],'.format(context.icon_filename)
        executables = []

        for input_filename in context.input_filenames:
            executables.append(textwrap.dedent(
                """\
                {{ "script" : r"{input}",
                 "dest_base" : "{name}",
                 # "other_resources" : [ (24, 1, manifest), ],
                 {version_info}
                {icon}
                }},
                """).format( input=input_filename,
                             name=os.path.splitext(os.path.basename(input_filename))[0],
                             version_info=version_info,
                             icon=icon_statement,
                           ))

        if context.build_type == cls.BuildType_Console:
            build_type = "console"
        elif context.build_type == cls.BuildType_Windows:
            build_type = "windows"
        else:
            assert False, context.build_type

        return textwrap.dedent(
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
                    {type}= [ 
                        {executables}
                    ],
                 )
            ''').format( paths='\n'.join([ 'sys.path.append("{}")'.format(os.path.abspath(path).replace('\\', '\\\\')) for path in context.paths ]),
                         manifest=StreamDecorator.LeftJustify( open(context.manifest_filename).read() if context.manifest_filename != None and os.path.isfile(context.manifest_filename) else textwrap.dedent(
                                                                        """\
                                                                        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                                                        <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0" />
                                                                        """).rstrip(),
                                                               4,
                                                             ),
                         name=os.path.splitext(os.path.basename(context.input_filenames[0]))[0],
                         optimize="0" if context.no_optimize else "2",
                         bundle="3" if context.no_bundle else "1",
                         optional_include_statement='' if not context.includes else '"includes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(include) for include in context.includes ])),
                         optional_exclude_statement='' if not context.excludes else '"excludes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(exclude) for exclude in context.excludes ])),
                         packages=', '.join([ '"{}"'.format(package) for package in context.packages ]),
                         type=build_type,
                         executables=StreamDecorator.LeftJustify(''.join(executables), 12),
                       )

    # ----------------------------------------------------------------------
    @staticmethod
    def _Compile(context, script_filename, output_stream):
        command_line = 'python "{}" py2exe{}'.format( script_filename,
                                                      '' if not context.distutil_args else " {}".format(' '.join([ '"{}"'.format(arg) for arg in context.distutil_args ])),
                                                    )

        result = Process.Execute(command_line, output_stream)
        if result == 0:
            FileSystem.RemoveTree("build")

            if os.path.isdir("dist"):
                FileSystem.RemoveTree(context.output_dir)
                shutil.move("dist", context.output_dir)

        return result

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
Compile                                     = CreateCompileMethod(Compiler)
Clean                                       = CreateCleanMethod(Compiler)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
