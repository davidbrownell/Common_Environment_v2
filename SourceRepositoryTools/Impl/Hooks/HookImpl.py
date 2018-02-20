# ----------------------------------------------------------------------
# |  
# |  HookImpl.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-10-24 17:17:06
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Hook implementation called within an activated environment window.
"""

import inspect
import json
import os
import sys

from collections import OrderedDict

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import Interface
from CommonEnvironment import Package
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "GeneratedCode"))
with CallOnExit(lambda: sys.path.pop(0)):
    import HooksImplParser                                                  # <Unable to import> pylint: disable = F0401

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools.Impl.ActivationActivity.IActivationActivity import IActivationActivity
    from SourceRepositoryTools.Impl.ActivationData import ActivationData
    from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( display_sentinel=CommandLine.StringTypeInfo(),
                                  json_filename=CommandLine.FilenameTypeInfo(),
                                  result_filename=CommandLine.FilenameTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def Commit( display_sentinel,
            json_filename,
            result_filename,
            first=False,
            output_stream=sys.stdout,
          ):
    return _Impl( display_sentinel,
                  json_filename,
                  result_filename,
                  first,
                  output_stream,
                  Constants.SETUP_ENVIRONMENT_COMMIT_HOOK_EVENT_HANDLER,
                  HooksImplParser.Commit_FromJson,
                )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( display_sentinel=CommandLine.StringTypeInfo(),
                                  json_filename=CommandLine.FilenameTypeInfo(),
                                  result_filename=CommandLine.FilenameTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def Push( display_sentinel,
          json_filename,
          result_filename,
          first=False,
          output_stream=sys.stdout,
        ):
    return _Impl( display_sentinel,
                  json_filename,
                  result_filename,
                  first,
                  output_stream,
                  Constants.SETUP_ENVIRONMENT_PUSH_HOOK_EVENT_HANDLER,
                  HooksImplParser.Push_FromJson,
                )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( display_sentinel=CommandLine.StringTypeInfo(),
                                  json_filename=CommandLine.FilenameTypeInfo(),
                                  result_filename=CommandLine.FilenameTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def Pushed( display_sentinel,
            json_filename,
            result_filename,
            first=False,
            output_stream=sys.stdout,
          ):
    return _Impl( display_sentinel,
                  json_filename,
                  result_filename,
                  first,
                  output_stream,
                  Constants.SETUP_ENVIRONMENT_PUSHED_HOOK_EVENT_HANDLER,
                  HooksImplParser.Pushed_FromJson,
                )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Impl( display_sentinel,
           json_filename,
           result_filename,
           first,
           output_stream,
           method_name,
           parser,
         ):
    output_stream = StreamDecorator( output_stream,
                                     line_prefix=display_sentinel,
                                   )

    with open(json_filename) as f:
        try:
            data = parser(f.read(), is_root=True)
        except Exception as ex:
            output_stream.write("ERORR: {} ({})\n".format(ex, ex.stack))
            return -1

    output_stream.write("Parsing dependencies...")
    with output_stream.DoneManager():
        dependencies = ActivationData.Load(None, None).PrioritizedRepos
    
    has_config_specific = False

    output_stream.write("Validating...")
    with output_stream.DoneManager() as dm:
        for repository_info in dependencies:
            with IActivationActivity.CustomMethodManager(os.path.join(repository_info.Root, Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME), method_name) as method:
                if not method:
                    continue

                args = { "data" : data,
                       }

                # Get the method args to see if a configuration is required
                func_code = six.get_function_code(method)

                if "configuration" in func_code.co_varnames[:func_code.co_argcount]:
                    args["configuration"] = configuration
                    has_config_specific = True
                elif not first:
                    # Don't call a config-agnostic method again if we aren't
                    # the first invocation.
                    continue

                try:
                    Interface.CreateCulledCallable(method)(args)

                except Exception as ex:
                    dm.stream.write(StreamDecorator.LeftJustify( "ERROR: {}\n".format(str(ex)),
                                                                 len("ERROR: "),
                                                               ))
                    dm.result = -1
                    return dm.result
        
        with open(result_filename, 'w') as f:
            f.write('1' if has_config_specific else '0')
        
        return dm.result 

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
