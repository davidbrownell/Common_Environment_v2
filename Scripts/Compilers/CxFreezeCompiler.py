# ----------------------------------------------------------------------
# |  
# |  CxFreezeCompiler.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-06-18 16:15:57
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import shutil
import sys
import textwrap

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Impl"))
with CallOnExit(lambda: sys.path.pop(0)):
    from DistutilsCompiler import ( CreateCompileMethod,
                                    CreateCleanMethod,
                                    DistutilsCompiler as CompilerBase,
                                  )

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
@Interface.staticderived
class Compiler(CompilerBase):
    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "CxFreezeCompiler"

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _GenerateScriptContent(cls, context):
        # Raise an error if unsupported attributes are populated
        for attribute_name in [ "comments",
                                "company_name",
                                "internal_name",
                              ]:
            if getattr(context, attribute_name):
                raise Exception("'{}' is not supported by this compiler".format(attribute_name))

        base = "Win32GUI" if sys.platform == "win32" and context.build_type == cls.BuildType_Windows else "None"
        icon_statement = "# No icon" if not context.icon_filename else '"icon" : r"{}",'.format(context.icon_filename)
        copyright_statement = "# No copyright" if not context.copyright else '"copyright" : "{}",'.format(context.copyright)
        trademarks_statement = "# No trademarks" if not context.trademarks else '"trademarks" : "{}",'.format(context.trademarks)

        executables = []

        for input_filename in context.input_filenames:
            executables.append(textwrap.dedent(
                """\
                Executable( r"{input}",
                            base={base},
                            {icon}
                            {copyright}
                            {trademarks}
                          ),
                """).format( input=input_filename,
                             base=base,
                             icon=icon_statement,
                             copyright=copyright_statement,
                             trademarks=trademarks_statement,
                           ))

        return textwrap.dedent(
            """\
            import sys
            from cx_Freeze import setup, Executable

            {paths}

            setup( name="{name}",
                   version="{version}",
                   description="{description}",
                   options={{ "build_exe" : {{ "optimize" : {optimize},
                                               "packages" : [ {packages} ],
                                               {optional_excludes}
                                               {optional_includes}
                                            }},
                           }},
                   executables=[ 
                        {executables}
                   ],
                 )
            """).format( paths='\n'.join([ 'sys.path.append("{}")'.format(os.path.abspath(path).replace('\\', '\\\\')) for path in context.paths ]),
                         name=context.name or os.path.splitext(os.path.basename(context.input_filenames[0]))[0],
                         version=context.version or "1.0.0.0",
                         description=context.file_description,
                         optimize="0" if context.no_optimize else "2",
                         packages=', '.join([ '"{}"'.format(package) for package in context.packages ]),
                         optional_excludes='' if not context.excludes else '"excludes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(exclude) for exclude in context.excludes ])),
                         optional_includes='' if not context.includes else '"includes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(include) for include in context.includes ])),
                         executables=StreamDecorator.LeftJustify(''.join(executables), 12),
                       )

    # ----------------------------------------------------------------------
    @staticmethod
    def _Compile(context, script_filename, output_stream):
        command_line = 'python "{}" build_exe{}'.format( script_filename,
                                                         '' if not context.distutil_args else " {}".format(' '.join([ '"{}"'.format(arg) for arg in context.distutil_args ])),
                                                       )

        result = Process.Execute(command_line, output_stream)
        if result == 0:
            if os.path.isdir("build"):
                subdirs = os.listdir("build")
                assert len(subdirs) == 1, subdirs

                source_dir = os.path.join("build", subdirs[0])

                # Remove empty dirs
                to_remove = []

                for root, dirs, _ in os.walk(source_dir):
                    for dir in dirs:
                        fullpath = os.path.join(root, dir)

                        if os.path.isdir(fullpath) and not os.listdir(fullpath):
                            to_remove.append(fullpath)

                for dir in to_remove:
                    os.rmdir(dir)

                FileSystem.RemoveTree(context.output_dir)
                shutil.move(source_dir, context.output_dir)
                FileSystem.RemoveTree("build")

        return result

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
Compile                                     = CreateCompileMethod(Compiler)
Clean                                       = CreateCleanMethod(Compiler)    

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass