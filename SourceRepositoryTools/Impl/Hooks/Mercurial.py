# ----------------------------------------------------------------------
# |  
# |  Mercurial.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-10-23 08:29:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
import json
import os
import sys
import textwrap
import time

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  Get the CommonEnvironment dir
def GetCommonEnvironment():
    if os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"):
        return os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
        
    generated_dir = os.path.join(os.getcwd(), "Generated")
    if not os.path.isdir(generated_dir):
        raise Exception("'{}' is not a valid directory".format(generated_dir))

    # Any configuration will do, as they will all point to the same file system location
    for item in os.listdir(generated_dir):
        fullpath = os.path.join(generated_dir, item)
        if os.path.isdir(fullpath):
            break

    fullpath = os.path.join(fullpath, "EnvironmentBootstrap.data")
    if not os.path.isfile(fullpath):
        raise Exception("'{}' is not a valid file".format(fullpath))

    development_root = None

    for line in open(fullpath).readlines():
        if line.startswith("fundamental_repo="):
            development_root = line[len("fundamental_repo="):].strip()
            break

    if development_root is None:
        raise Exception("The development root was not found")

    development_root = os.path.realpath(os.path.join(os.getcwd(), development_root))
    if not os.path.isdir(development_root):
        raise Exception("'{}' is not a valid development root".format(development_root))

    return development_root
 
_common_environment = GetCommonEnvironment()
del GetCommonEnvironment
                
# ----------------------------------------------------------------------
def PreTxnCommit(ui, repo, node, parent1, parent2, *args, **kwargs):
    is_debug = _IsDebug(ui)

    if is_debug:
        ui.write(textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            PreTxnCommit
            
            Repo Root:      {}
            node:           {}
            parent 1:       {}
            parent 2:       {}
            args:           {}
            kwargs:         {}

            # ----------------------------------------------------------------------
            """).format( repo.root,
                         node,
                         parent1,
                         parent2,
                         args,
                         kwargs,
                       ))

    # If parent2 is valid, we are looking at a merge. No need to
    # get the extra data.
    
    return _Impl( ui,
                  "Commit",
                  _GetChangeInfo(repo, repo[node]),
                  is_debug,
                )

# ----------------------------------------------------------------------
def PreOutgoing(ui, repo, source, *args, **kwargs):
    return 0 # Disabling hooks for now

    # Only process push data
    if source != "push":
        return 0

    is_debug = _IsDebug(ui)

    if is_debug:
        ui.write(textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            PreOutgoing
            
            Repo Root:      {}
            args:           {}
            kwargs:         {}

            # ----------------------------------------------------------------------
            """).format( repo.root,
                         source,
                         args,
                         kwargs,
                       ))

    data = {}

    if "url" in kwargs:
        data["url"] = kwargs["url"]

    return _Impl( ui,
                  "Push",
                  data,
                  is_debug,
                )

# ----------------------------------------------------------------------
def PreTxnChangeGroup(ui, repo, source, node, node_last, *args, **kwargs):
    return 0 # Disabling hooks for now

    if source != "serve":
        return 0

    is_debug = _IsDebug(ui)

    if is_debug:
        ui.write(textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            PreTxnChangeGroup
            
            Repo Root:      {}
            node:           {}
            node_last:      {}
            args:           {}
            kwargs:         {}

            # ----------------------------------------------------------------------
            """).format( repo.root,
                         node,
                         node_last,
                         args,
                         kwargs,
                       ))
    
    changes = []
    queue = [ node, ]
    visited = set()

    while queue:
        node = queue.pop()
        ctx = repo[node]

        changes.append(_GetChangeInfo(repo, ctx))
        visited.add(node)

        for child in ctx.children():
            if child in visited:
                continue

            queue.append(child)

    changes.sort(key=lambda c: c["date"])

    return _Impl( ui,
                  "Pushed",
                  { "changes" : changes,
                  },
                  is_debug,
                )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Impl(ui, verb, json_content, is_debug):
    try:
        import mercurial

        mercurial.demandimport.disable()
    except:
        pass

    # Imports here can be tricky
    try:
        sys.path.insert(0, os.path.join(_common_environment))

        from SourceRepositoryTools.Impl import CommonEnvironmentImports
        from SourceRepositoryTools.Impl import Constants

        del sys.path[0]
    except:
        import traceback

        ui.write(traceback.format_exc())
        raise
    
    environment = CommonEnvironmentImports.Shell.GetEnvironment()
    output_stream = CommonEnvironmentImports.StreamDecorator(ui)
    
    output_stream.write("Getting configurations...")
    with output_stream.DoneManager() as dm:
        activation_script = os.path.join(os.getcwd(), Constants.ACTIVATE_ENVIRONMENT_NAME) + environment.ScriptExtension
        if not os.path.isfile(activation_script):
            return 0

        rval, output = CommonEnvironmentImports.Process.Execute("{} ListConfigurations json".format(activation_script))
        assert rval == 0

        data = json.loads(output)
        
        configurations = list(data.keys())
        if not configurations:
            configurations = [ "None", ]

    output_stream.write("Processing configurations...")
    with output_stream.DoneManager( done_suffix='\n',
                                  ) as dm:
        display_sentinel = "Display?!__ "
        display_sentinel_len = len(display_sentinel)

        json_filename = environment.CreateTempFilename(".json")
        
        with open(json_filename, 'w') as f:
            json.dump(json_content, f)

        skip = False

        with CommonEnvironmentImports.CallOnExit(lambda: os.remove(json_filename)):
            original_environment = None
            
            if os.getenv(Constants.DE_REPO_GENERATED_NAME):
                # This code sucks because it is hard coding names and duplicating logic in ActivateEnvironment. However, importing
                # ActivateEnvironment here is causing problems, as the Mercurial version of python is different enough from our
                # version that some imports don't work between python 2 and python 3.
                original_data_filename = os.path.join(os.getenv(Constants.DE_REPO_GENERATED_NAME), "OriginalEnvironment.json")
                assert os.path.isfile(original_data_filename), original_data_filename
                
                with open(original_data_filename) as f:
                    original_environment = json.load(f)
                
            for index, configuration in enumerate(configurations):
                dm.stream.write("Configuration '{}' ({} of {})...".format( configuration if configuration != "None" else "<default>",
                                                                           index + 1,
                                                                           len(configurations),
                                                                         ))
                with dm.stream.DoneManager() as this_dm:
                    if skip:
                        continue

                    result_filename = environment.CreateTempFilename()

                    # ----------------------------------------------------------------------
                    def RemoveResultFilename():
                        if os.path.isfile(result_filename):
                            os.remove(result_filename)

                    # ----------------------------------------------------------------------

                    with CommonEnvironmentImports.CallOnExit(RemoveResultFilename):
                        commands = [ CommonEnvironmentImports.Shell.EchoOff(),
                                     CommonEnvironmentImports.Shell.Raw('cd "{}"'.format(os.path.dirname(activation_script))),
                                     CommonEnvironmentImports.Shell.Call("{} {}".format(os.path.basename(activation_script), configuration if configuration != "None" else '')),
                                     CommonEnvironmentImports.Shell.ExitOnError(-1),
                                     CommonEnvironmentImports.Shell.Set( "PYTHONPATH",
                                                                         _common_environment,
                                                                         preserve_original=False,
                                                                       ),
                                     CommonEnvironmentImports.Shell.Raw('python -m SourceRepositoryTools.Impl.Hooks.HookImpl "{verb}" "{sentinel}" "{json_filename}" "{result_filename}"{first}' \
                                                                            .format( verb=verb,
                                                                                     sentinel=display_sentinel,
                                                                                     json_filename=json_filename,
                                                                                     result_filename=result_filename,
                                                                                     first=" /first" if index == 0 else '',
                                                                                   )),
                                     CommonEnvironmentImports.Shell.Set( "PYTHONPATH",
                                                                         None,
                                                                         preserve_original=False,
                                                                       ),
                                   ]
        
                        script_filename = environment.CreateTempFilename(environment.ScriptExtension)
                        with open(script_filename, 'w') as f:
                            f.write(environment.GenerateCommands(commands))
            
                        with CommonEnvironmentImports.CallOnExit(lambda: CommonEnvironmentImports.FileSystem.RemoveFile(script_filename)):
                            environment.MakeFileExecutable(script_filename)
            
                            content = []
            
                            # ----------------------------------------------------------------------
                            def Display(s):
                                if s.startswith(display_sentinel):
                                    s = s[display_sentinel_len:]
                                    this_dm.stream.write(s)
                                    this_dm.stream.flush()

                                content.append(s)
            
                            # ----------------------------------------------------------------------

                            this_dm.result = CommonEnvironmentImports.Process.Execute( script_filename, 
                                                                                       Display,
                                                                                       line_delimited_output=True,
                                                                                       environment=original_environment,
                                                                                     )

                            if is_debug:
                                this_dm.stream.write(''.join(content))
                                
                            if this_dm.result == -1:
                                return this_dm.result
                            
                            assert os.path.isfile(result_filename), result_filename
                            result = open(result_filename).read()
                            
                            if result == "1":
                                skip = True
                            elif result == "0":
                                pass
                            else:
                                assert False, result

        return dm.result
        
# ----------------------------------------------------------------------
def _IsDebug(ui):
    return ui.config("ui", "debug", default='').strip().lower() == "true"

# ----------------------------------------------------------------------
def _GetChangeInfo(repo, ctx):
    # ----------------------------------------------------------------------
    def TransformFilename(filename):
        return os.path.join(repo.root, filename).replace('/', os.path.sep)

    # ----------------------------------------------------------------------

    parents = ctx.parents()
    if not parents:
        parents = [ None, ]

    status = repo.status(parents[0], ctx)

    t, tz = ctx.date()
    t = time.gmtime(t - tz)
    t = datetime.datetime(*t[:6])

    return { "id" : ctx.hex(),
             "author" : ctx.user(),
             "date" : t.isoformat(),
             "description" : ctx.description(),
             "branch" : ctx.branch(),
             "added" : [ TransformFilename(filename) for filename in status.added ],
             "modified" : [ TransformFilename(filename) for filename in status.modified ],
             "removed" : [ TransformFilename(filename) for filename in status.removed ],
           }
