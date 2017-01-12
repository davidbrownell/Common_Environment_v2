# ---------------------------------------------------------------------------
# |  
# |  ZipInstallerCompiler.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  01/13/2016 07:45:23 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""ZipInstaller compiler
"""

import os
import subprocess
import sys
import textwrap
import zipfile

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
from CommonEnvironment.Compiler.OutputMixin.SingleOutputMixin import SingleOutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

try:
    import zlib
    zip_compression = zipfile.ZIP_DEFLATED
except ImportError:
    zip_compression = zipfile.ZIP_STORED

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived
class Compiler( AtomicInputProcessingMixin,
                AlwaysInvocationQueryMixin,
                CustomInvocationMixin,
                SingleOutputMixin,
                CompilerMod.Compiler,
              ):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "ZipInstallerCompiler"
    Description                             = "Creates an install package using ZipInstaller"
    Type                                    = CompilerMod.Compiler.TypeValue.Directory

    ( InstallTo_AllUsers,
      InstallTo_CurrentUser,
    ) = range(2)

    DefaultInstallFolder                    = r"%zi.ProgramFiles%\%zi.CompanyName%\%zi.ProductName%"
    DefaultStartMenuFolder                  = r"%zi.CompanyName%\%zi.ProductName%"

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
        return os.path.isdir(item)

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetRequiredContextNames(cls):
        return [ "product_name",
                 "product_version",
                 "company_name",
                 "output_dir", 
               ] + \
               super(Compiler, cls)._GetRequiredContextNames()

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetOptionalMetadata(cls):
        return { "output_name" : None,
                 "description" : None,
                 "install_to" : cls.InstallTo_CurrentUser,
                 "desktop_shortcut" : False,
                 "start_menu_shortcut" : True,
                 "add_uninstall" : True,
                 "add_uninstall_shortcut" : False,
                 "install_folder" : cls.DefaultInstallFolder,
                 "start_menu_folder" : cls.DefaultStartMenuFolder,
                 "no_extra_uninstall_info" : False,
                 "no_success_message" : False,
                 "no_user_interaction" : False,
               }

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        if not context.output_name:
            context.output_name = context.product_name

        context.output_filename = os.path.join(context.output_dir, "{}.exe".format(context.output_name))

        return super(Compiler, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl(cls, invoke_reason, context, status_stream, verbose_stream, verbose):
        if not os.path.isdir(os.path.dirname(context.output_filename)):
            os.makedirs(os.path.dirname(context.output_filename))

        zip_filename = Shell.GetEnvironment().CreateTempFilename(".zip")
        
        # Write the configuration file
        config_filename = os.path.join(context.input_dirs[0], "~zipinst~.zic")
        with open(config_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                [install]
                ProductName={product_name}
                ProductVersion={product_version}
                CompanyName={company_name}
                Description={description}
                InstallTo={install_to}
                DesktopShortcut={desktop_shortcut}
                StartMenuShortcut={startmenu_shortcut}
                AddUninstall={add_uninstall}
                AddUninstallShortcut={add_uninstall_shortcut}
                InstallFolder={install_folder}
                StartMenuFolder={start_menu_folder}
                NoExtraUninstallInfo={no_extra_uninstall_info}
                NoSuccessMessage={no_success_message}
                NoUserInteraction={no_user_interaction}
                """).format( product_name=context.product_name,
                             product_version=context.product_version,
                             company_name=context.company_name,
                             description=context.description or '',
                             install_to=1 if context.install_to == cls.InstallTo_AllUsers else 2,
                             desktop_shortcut=1 if context.desktop_shortcut else 0,
                             startmenu_shortcut=1 if context.start_menu_shortcut else 0,
                             add_uninstall=1 if context.add_uninstall else 0,
                             add_uninstall_shortcut=1 if context.add_uninstall_shortcut else 0,
                             install_folder=context.install_folder,
                             start_menu_folder=context.start_menu_folder,
                             no_extra_uninstall_info=1 if context.no_extra_uninstall_info else 0,
                             no_success_message=1 if context.no_success_message else 0,
                             no_user_interaction=1 if context.no_user_interaction else 0,
                           ))

        with CallOnExit(lambda: os.remove(config_filename)):
            status_stream.write("Creating zip file...")
            with status_stream.DoneManager(associated_stream=verbose_stream) as (dm, this_verbose_stream):
                common_prefix = FileSystem.Normalize(os.path.commonprefix(context.input_dirs))
                if not common_prefix:
                    common_prefix = FileSystem.GetCommonPath(*context.input_dirs)
                else:
                    common_prefix += os.path.sep

                current_dir = os.getcwd()
                os.chdir(common_prefix)
                with CallOnExit(lambda: os.chdir(current_dir)):
                    with zipfile.ZipFile(zip_filename, mode='w') as zf:
                        for index, input_dir in enumerate(context.input_dirs):
                            this_verbose_stream.write("Adding '{}' ({} of {})...".format(input_dir, index + 1, len(context.input_dirs)))
                            with this_verbose_stream.DoneManager() as dir_dm:
                                for filename in FileSystem.WalkFiles(input_dir):
                                    item_name = filename
                                    if common_prefix:
                                        assert filename.lower().startswith(common_prefix.lower()), (filename, common_prefix)
                                        item_name = item_name[len(common_prefix):]

                                        zf.write(item_name, compress_type=zip_compression)

        # Create the installation file
        with CallOnExit(lambda: os.remove(zip_filename)):
            status_stream.write("Creating installer...")
            with status_stream.DoneManager(associated_stream=verbose_stream) as (dm, this_verbose_stream):
                command_line = 'zipinst /selfexe "{zip_filename}" "{output_filename}"'   \
                                    .format( zip_filename=zip_filename,
                                             output_filename=context.output_filename,
                                           )

                result = subprocess.Popen( command_line,
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                         )

                sink = StringIO()
                immediate_output_stream = StreamDecorator([ sink, this_verbose_stream, ])

                while True:
                    line = result.stdout.readline()
                    if not line:
                        break

                    immediate_output_stream.write(line)

                dm.result = result.wait() or 0
                if dm.result != 0 and not verbose:
                    status_stream.write(sink.getvalue())

                return dm.result

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.DirectoryTypeInfo(arity='+'),
                                  product_name=CommandLine.StringTypeInfo(),
                                  product_version=CommandLine.StringTypeInfo(),
                                  company_name=CommandLine.StringTypeInfo(),
                                  output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  output_name=CommandLine.StringTypeInfo(arity='?'),
                                  description=CommandLine.StringTypeInfo(arity='?'),
                                  install_to=CommandLine.EnumTypeInfo([ "CurrentUser", "AllUsers", ], arity='?'),
                                  output_stream=None,
                                )
def Compile( input,
             product_name,
             product_version,
             company_name,
             output_dir,
             output_name=None,
             description=None,
             install_to="CurrentUser",
             desktop_shortcut=False,
             uninstall_shortcut=False,
             no_start_menu_shortcut=False,
             no_uninstall=False,
             install_folder=Compiler.DefaultInstallFolder,
             start_menu_folder=Compiler.DefaultStartMenuFolder,
             no_extra_uninstall_info=False,
             no_success_message=False,
             no_user_interaction=False,
             output_stream=sys.stdout,
             verbose=False,
           ):

    if install_to == "CurrentUser":
        install_to = Compiler.InstallTo_CurrentUser
    elif install_to == "AllUsers":
        install_to = Compiler.InstallTo_AllUsers
    else:
        assert False

    return CompilerMod.CommandLineCompile( Compiler,
                                           input,
                                           output_stream,
                                           verbose,

                                           product_name=product_name,
                                           product_version=product_version,
                                           company_name=company_name,
                                           output_dir=output_dir,
                                           output_name=output_name,
                                           description=description,
                                           install_to=install_to,
                                           desktop_shortcut=desktop_shortcut,
                                           add_uninstall_shortcut=uninstall_shortcut,
                                           start_menu_shortcut=not no_start_menu_shortcut,
                                           add_uninstall=not no_uninstall,
                                           install_folder=install_folder,
                                           start_menu_folder=start_menu_folder,
                                           no_extra_uninstall_info=no_extra_uninstall_info,
                                           no_success_message=no_success_message,
                                           no_user_interaction=no_user_interaction,
                                         )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.DirectoryTypeInfo(arity='+'),
                                  output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  output_name=CommandLine.StringTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Clean( input,
           output_dir,
           output_name=None,
           output_stream=sys.stdout,
           verbose=False,
         ):
    return CompilerMod.CommandLineClean( Compiler,
                                         input,
                                         output_stream,
                                         verbose,

                                         output_dir=output_dir,
                                         output_name=output_name,
                                       )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
