# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/30/2015 04:04:59 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import shutil
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import Process
from CommonEnvironment import TaskPool
from CommonEnvironment import Shell
from CommonEnvironment import SourceControlManagement
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    import SourceRepositoryTools                        # <Unable to import> pylint: disable = F0401
    from SourceRepositoryTools import Constants         # <Unable to import> pylint: disable = F0401

# ----------------------------------------------------------------------
# <Too many local variables> pylint: disable = R0914

inflect                                     = inflect_mod.engine()

# ---------------------------------------------------------------------------
def NormalizeRepoTemplates(code_root, *repo_templates_params):
    """\
    Repo templates can be a list of items, where an item is a repository-specific
    connection string or GUID. If the item is a GUID, this indicates a dependency
    repository where all of the repositories listed in that repository's EnlistAll.py
    script should be considered as dependencies of this repository as well. Note that
    this functionality is recursive.
    """
    
    code_root = os.path.normpath(code_root)

    repo_templates = []

    guid_re = re.compile(r"[0-9A-Fa-f]{32}")
    Template = NamedTuple("Template", "uri", "branch", "setup_configurations")

    # ---------------------------------------------------------------------------
    def AddTemplate(uri, branch, setup_configurations):
        if next((item for item in repo_templates if item.uri == uri), None) == None:
            repo_templates.append(Template(uri, branch, setup_configurations))

    # ---------------------------------------------------------------------------
    
    dependency_map = None

    for repo_template in repo_templates_params:
        if isinstance(repo_template, tuple):
            if len(repo_template) == 1:
                uri = repo_template
                branch = None
                setup_configurations = None

            elif len(repo_template) == 2:
                uri, branch = repo_template
                setup_configurations = None

            elif len(repo_template) == 3:
                uri, branch, setup_configurations = repo_template

            else:
                assert False, repo_template

        else:
            uri = repo_template
            branch = None
            setup_configurations = None

        if not guid_re.match(uri):
            AddTemplate(uri, branch, setup_configurations)
            continue
    
        # Extract repositories by invoking the repo's EnlistAll script
        if dependency_map == None:
            dependency_map = SourceRepositoryTools.CreateDependencyMap(code_root)

        assert uri in dependency_map, uri
        repo_root = dependency_map[uri].root

        repo_enlist_all = os.path.join(repo_root, Constants.SCRIPTS_SUBDIR, "EnlistAll.py")
        assert os.path.isfile(repo_enlist_all), repo_enlist_all

        result, content = Process.Execute('python "{}" List /verbose /no_populate'.format(repo_enlist_all),)
        assert result == 0, result
        
        for line in [ line.strip() for line in content.split('\n') if line.strip() ]:
            values = line.split(';')
            assert len(values) == 3, line

            uri = values[0].strip()
            branch = values[1].strip()

            if branch.lower() == "none":
                branch = None

            setup_configurations = values[2].strip()
            if setup_configurations.lower() == "none":
                setup_configurations = None

            AddTemplate(uri, branch, setup_configurations)

    return repo_templates

# ---------------------------------------------------------------------------
def ListFunctionFactory( repo_templates,
                         config_params,
                         output_stream=sys.stdout,
                       ):
    repo_templates = _NormalizeRepoTemplates(repo_templates)

    # ---------------------------------------------------------------------------
    def Impl( no_populate,
              verbose,
              **kwargs
            ):
        output_stream.write('\n')

        if verbose:
            output_stream.write('\n'.join([ "{}; {}; {}".format( repo.uri,
                                                                 repo.branch,
                                                                 repo.setup_configurations,
                                                               )
                                            for repo in repo_templates
                                          ]))
        else:
            output_stream.write('\n'.join([ (repo.uri if no_populate else repo.uri.format(**kwargs))
                                            for repo in repo_templates
                                          ]))

        output_stream.write('\n')

    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "List",
                                   config_params,
                                   Impl,
                                   suffix_args=[ ( "no_populate", False ),
                                                 ( "verbose", False ),
                                               ],
                                 )
    
# ---------------------------------------------------------------------------
def MatchFunctionFactory( repo_templates,
                          config_params,
                          output_stream=sys.stdout,
                        ):
    repo_templates = _NormalizeRepoTemplates(repo_templates)
    
    # ---------------------------------------------------------------------------
    def Impl( code_root,
              **kwargs
            ):
        output_stream.write("Searching for repositories in '{}'...".format(code_root))
        with StreamDecorator(output_stream).DoneManager(done_suffix='\n'):
            diff = _CalculateRepoDiff( code_root,
                                       repo_templates,
                                       kwargs,
                                     )

        if not diff.local_only and not diff.reference_only:
            output_stream.write("All repositories were found on the local machine.\n")
        else:
            output_stream.write(textwrap.dedent(
                """\

                The following repositories matched ({}):
                {}
                """).format( len(diff.matches),
                             '\n'.join([ "    - {} <{}> [{}, {}] ".format( repo.path, 
                                                                           repo.uri, 
                                                                           repo.branch, 
                                                                           repo.setup_configurations,
                                                                         )
                                         for repo in diff.matches
                                       ]),
                           ))

            if diff.local_only:
                output_stream.write(textwrap.dedent(
                    """\
                    
                    The following repositories were found on the local machine but not in the master list ({}):
                    {}
                    """).format( len(diff.local_only),
                                 '\n'.join([ "    - {} <{}>".format(repo.path, repo.uri) for repo in diff.local_only ]),
                               ))

            if diff.reference_only:
                output_stream.write(textwrap.dedent(
                    """\
                    
                    The following repositories were in the master list but not on the local machine ({}):
                    {}
                    """).format( len(diff.reference_only),
                                 '\n'.join([ "    - {}".format("{} [{}]".format(uri, branch) if branch else uri) for uri, branch in diff.reference_only ]),
                               ))
        
        incorrect_branches = []

        for repo in diff.matches:
            if not repo.branch:
                continue

            expected_branch_name = repo.branch
            actual_branch_name = repo.scm.GetCurrentBranch(repo.path)

            if actual_branch_name != expected_branch_name:
                incorrect_branches.append((repo.path, expected_branch_name, actual_branch_name))
        
        if incorrect_branches:
            output_stream.write(textwrap.dedent(
                """\
                
                The following local repositories are not set to the correct branch:
                {}
                """).format('\n'.join([ "    - {} [Expected: {}, Actual: {}]".format(path, expected, actual) for path, expected, actual in incorrect_branches ])))                           

    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "Match",
                                   config_params,
                                   Impl,
                                   prefix_args=[ ( "code_root", _NoDefault, CommandLine.DirectoryTypeInfo() ),
                                               ],
                                 )

# ---------------------------------------------------------------------------
def EnlistFunctionFactory( repo_templates,
                           config_params,
                           output_stream_param=sys.stdout,
                         ):
    repo_templates = _NormalizeRepoTemplates(repo_templates)
    potential_scms = SourceControlManagement.GetPotentialSCMs()

    # ---------------------------------------------------------------------------
    def Impl( code_root,
              scm='',
              branch_name=None,
              remove_extra_repos=False,
              preserve_branches=False,
              flat=False,
              no_status=False,
              preserve_ansi_escape_sequences=False,
              **kwargs
            ):
        with StreamDecorator.GenerateAnsiSequenceStream( output_stream_param,
                                                         preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                                                       ) as output_stream:
            with output_stream.DoneManager( line_prefix='',
                                            done_prefix="\nResults: ",
                                            done_suffix='\n',
                                          ) as dm:
                scm = next(obj for obj in potential_scms if obj.Name == scm)

                dm.stream.write("Searching for repositories in '{}'...".format(code_root))
                with dm.stream.DoneManager( done_suffix_functor=lambda: "{} found".format(inflect.no("repository", len(diff.matches) + len(diff.local_only) + len(diff.reference_only))),
                                          ):
                    diff = _CalculateRepoDiff( code_root,
                                               repo_templates,
                                               kwargs,
                                             )

                if diff.matches:
                    with dm.stream.SingleLineDoneManager( "Updating {}...".format(inflect.no("repository", len(diff.matches))),
                                                        ) as update_dm:
                        # ----------------------------------------------------------------------
                        def Invoke(task_index, output_stream, on_status_update):
                            on_status_update = (lambda value: None) if no_status else on_status_update
                    
                            repo = diff.matches[task_index]
                    
                            current_branch_name = repo.scm.GetCurrentBranch(repo.path)
                            repo_branch_name = branch_name or repo.branch or (current_branch_name if preserve_branches else repo.scm.DefaultBranch)
                    
                            if preserve_branches and current_branch_name != repo_branch_name:
                                restore_branch_name = current_branch_name
                            else:
                                restore_branch_name = None
                    
                            # Set the branch
                            on_status_update("Setting branch to '{}'".format(repo_branch_name))
                    
                            result, output = repo.scm.SetBranch(repo.path, repo_branch_name)
                            output_stream.write(output)
                            if result != 0:
                                return result
                    
                            # Pull changes
                            if repo.scm.IsDistributed:
                                on_status_update("Pulling changes")
                    
                                result, output = repo.scm.Pull(repo.path)
                                output_stream.write(output)
                                if result != 0:
                                    return result
                    
                            # Update
                            on_status_update("Updating")
                    
                            result, output = repo.scm.Update(repo.path, SourceControlManagement.EmptyUpdateMergeArg())
                            output_stream.write(output)
                            if result != 0:
                                return result
                    
                            # Restore
                            if restore_branch_name is not None:
                                on_status_update("Restoring branch to '{}'".format(restore_branch_name))
                    
                                result, output = repo.scm.SetBranch(repo.path, restore_branch_name)
                                output_stream.write(output)
                                if result != 0:
                                    return result
                    
                            return 0
                    
                        # ----------------------------------------------------------------------
                    
                        update_dm.result = TaskPool.Execute( [ TaskPool.Task( repo.path,
                                                                              "Processing '{}'".format(repo.path),
                                                                              Invoke,
                                                                            )
                                                               for repo in diff.matches
                                                             ],
                                                             output_stream=update_dm.stream,
                                                             progress_bar=True,
                                                           )
                        if update_dm.result != 0:
                            return update_dm.result

                # Remove extra repos
                if remove_extra_repos and diff.local_only:
                    with dm.stream.SingleLineDoneManager( "Removing {}...".format(inflect.no("repository", len(diff.local_only))),
                                                        ) as remove_dm:
                        # ----------------------------------------------------------------------
                        def Invoke(task_index, on_status_update):
                            repo = diff.local_only[task_index]

                            if not no_status:
                                on_status_update(repo.path)

                            FileSystem.RemoveTree(repo.path)

                        # ----------------------------------------------------------------------

                        remove_dm.result = TaskPool.Execute( [ TaskPool.Task( repo.path,
                                                                              "Processing '{}'".format(repo.path),
                                                                              Invoke,
                                                                            )
                                                               for repo in diff.local_only
                                                             ],
                                                             num_concurrent_tasks=1,            # Only 1 thread as the activity invokes the disk
                                                             output_stream=remove_dm.stream,
                                                             progress_bar=True,
                                                           )
                        if remove_dm.result != 0:
                            return remove_dm.result

                # Clone
                if diff.reference_only:
                    with dm.stream.SingleLineDoneManager( "Cloning {}...".format(inflect.no("repository", len(diff.reference_only))),
                                                        ) as clone_dm:
                        # ----------------------------------------------------------------------
                        def Invoke(task_index, output_stream, on_status_update):
                            on_status_update = (lambda value: None) if no_status else on_status_update

                            uri, branch = diff.reference_only[task_index]

                            name = uri[uri.rfind('/') + 1:]

                            if flat:
                                output_dir = os.path.join(code_root, name)
                            else:
                                output_dir = os.path.join(code_root, *name.split('_'))

                            # Clone
                            on_status_update("Cloning '{}'".format(name))

                            result, output = scm.Clone(uri, output_dir, branch=branch)
                            output_stream.write(output)
                            if result != 0:
                                return result

                            if branch:
                                on_status_update("Setting branch to '{}'".format(branch))

                                result, output = scm.SetBranch(output_dir, branch)
                                output_stream.write(output)
                                if result != 0:
                                    return result

                            return 0

                        # ----------------------------------------------------------------------

                        clone_dm.result = TaskPool.Execute( [ TaskPool.Task( uri,
                                                                             "Processing '{}'".format(uri),
                                                                             Invoke,
                                                                           )
                                                              for uri, branch in diff.reference_only
                                                            ],
                                                            num_concurrent_tasks=1,             # Only 1 thread as the activity invokes the disk
                                                            output_stream=clone_dm.stream,
                                                            progress_bar=True,
                                                          )
                        if clone_dm.result != 0:
                            return clone_dm.result

                return dm.result
    
    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "Enlist",
                                   config_params,
                                   Impl,
                                   prefix_args=[ ( "code_root", _NoDefault, CommandLine.DirectoryTypeInfo() ),
                                                 ( "scm", '"{}"'.format(potential_scms[0].Name), CommandLine.EnumTypeInfo(values=[ scm.Name for scm in potential_scms ], arity='?') ),
                                                 ( "branch_name", None, CommandLine.StringTypeInfo(arity='?') ),
                                               ],
                                   suffix_args=[ ( "remove_extra_repos", False ),
                                                 ( "preserve_branches", False ),
                                                 ( "flat", False ),
                                                 ( "no_status", False ),
                                                 ( "preserve_ansi_escape_sequences", False ),
                                               ],
                                 )
              
# ---------------------------------------------------------------------------
# Note that this function doesn't necessarily have to be here, as it isn't implemented
# in terms of any of the functionality local to this file. However, it is logically consistent
# to place it here, as the functionality will be exposed by most derived scripts.
def SetupFunctionFactory( repo_templates,
                          config_params,
                          output_stream=sys.stdout,
                        ):
    repo_templates = _NormalizeRepoTemplates(repo_templates)

    # ---------------------------------------------------------------------------
    def Impl( code_root,
              **kwargs
            ):
        output_stream.write("Searching for repositories in '{}'...".format(code_root))
        with StreamDecorator(output_stream).DoneManager(done_suffix='\n'):
            diff = _CalculateRepoDiff( code_root,
                                       repo_templates,
                                       kwargs,
                                     )

        if not diff.matches:
            return 

        setup_environment_script = Shell.GetEnvironment().CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME)
                
        with StreamDecorator(output_stream).DoneManager( line_prefix='', 
                                                         done_prefix='\n\nComposite Results: ', 
                                                         done_suffix='\n',
                                                       ) as dm:
            for index, repo in enumerate(diff.matches):
                filename = os.path.join(repo.path, setup_environment_script)
                assert os.path.isfile(filename), filename

                title = "Running '{}' ({} of {})...".format(filename, index + 1, len(diff.matches))
                dm.stream.write("\n{}\n{}".format(title, '=' * len(title)))
                with dm.stream.DoneManager() as this_dm:
                    command_line = filename

                    if repo.setup_configurations:
                        command_line += " {}".format(' '.join([ '"/configuration={}"'.format(config) for config in repo.setup_configurations ]))

                    this_dm.result = Process.Execute(command_line, this_dm.stream)

        return dm.result

    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "Setup",
                                   config_params,
                                   Impl,
                                   prefix_args=[ ( "code_root", _NoDefault, CommandLine.DirectoryTypeInfo() ),
                                               ],
                                 )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class _NoDefault(object):
    pass

# ---------------------------------------------------------------------------
def _DefineDynamicFunction( func_name,
                            config_params,
                            impl_func,
                            prefix_args=None,
                            suffix_args=None,
                          ):
    constraint_params = OrderedDict()
    params = OrderedDict()

    # ---------------------------------------------------------------------------
    def ApplyArgs(args):
        for arg in (args or []):
            assert isinstance(arg, tuple)

            name = arg[0]
            
            params[name] = arg[1]

            if len(arg) > 2:
                constraint_params[name] = arg[2]

    # ---------------------------------------------------------------------------
    
    ApplyArgs(prefix_args)

    for k, v in six.iteritems(config_params):
        constraint_params[k] = CommandLine.StringTypeInfo(arity='?')
        params[k] = '"{}"'.format(v)

    ApplyArgs(suffix_args)

    d = { "CommandLine" : CommandLine,
          "constraint_params" : constraint_params,
          "Impl" : impl_func,
          func_name : None,
        }

    statement = textwrap.dedent(
        """\
        @CommandLine.EntryPoint(){constraints}
        def {name}({params}):
            return Impl({args})
        """).format( name=func_name,
                     constraints='' if not constraint_params else "\n@CommandLine.FunctionConstraints(**constraint_params)",
                     params=', '.join([ "{}{}".format(k, '' if v == _NoDefault else "={}".format(v)) for k, v in six.iteritems(params) ]),
                     args=', '.join([ "{k}={k}".format(k=k) for k in six.iterkeys(params) ]),
                   )
                  
    six.exec_(statement, d)

    return d[func_name]

# ---------------------------------------------------------------------------
def _NormalizeRepoTemplates(repo_templates):
    # Ensure that we only have 1 instance of each item
    lookup = OrderedDict()

    for index, repo_template in enumerate(repo_templates):
        if isinstance(repo_template, str):
            repo_templates[index] = NormalizeRepoTemplates(repo_template)[0]
            repo_template = repo_templates[index]

        if repo_template.uri in lookup and lookup[repo_template.uri].branch != repo_template.branch:
            raise Exception("The repository '{}' has been requested more than once with different branches ({}, {})".format( repo_template.uri,
                                                                                                                             lookup[repo_template.uri].branch,
                                                                                                                             repo_template.branch,
                                                                                                                           ))

        lookup[repo_template.uri] = repo_template

    return repo_templates

# ---------------------------------------------------------------------------
def _CalculateRepoDiff( code_root,
                        repo_templates,
                        kwargs,
                      ):
    RepoInfo = NamedTuple("RepoInfo", "scm", "uri", "branch", "setup_configurations", path=None)

    matches = []
    local_only = []

    repo_uri_lookup = OrderedDict()
    
    for repo_template in repo_templates:
        uri = repo_template.uri.format(**kwargs)
        
        repo_uri_lookup[uri.lower()] = (uri, repo_template)
    
    for scm, root in SourceControlManagement.EnumSCMDirectories(code_root):
        uri = scm.GetUniqueName(root)
        
        result = repo_uri_lookup.get(uri.lower(), None)
        if result:
            uri, repo = result

            matches.append(RepoInfo(scm, uri, repo.branch or scm.DefaultBranch, repo.setup_configurations, path=root))
            del repo_uri_lookup[uri.lower()]
        else:
            local_only.append(RepoInfo(scm, uri, scm.GetCurrentBranch(root), None, path=root))

    return QuickObject( matches=matches,
                        local_only=local_only,
                        reference_only=[ (uri, repo.branch) for uri, repo in six.itervalues(repo_uri_lookup) ],
                      )
