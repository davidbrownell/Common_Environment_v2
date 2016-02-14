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
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import subprocess
import shutil
import sys
import textwrap

from collections import OrderedDict

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment.QuickObject import QuickObject
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
    import SourceRepositoryTools

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

        repo_enlist_all = os.path.join(repo_root, SourceRepositoryTools.SCRIPTS_SUBDIR, "EnlistAll.py")
        assert os.path.isfile(repo_enlist_all), repo_enlist_all

        result = subprocess.Popen( 'python "{}" List /verbose /no_populate'.format(repo_enlist_all),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                 )
        content = result.stdout.read()
        assert (result.wait() or 0) == 0

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
              **vars
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
            output_stream.write('\n'.join([ (repo.uri if no_populate else repo.uri.format(**vars))
                                            for repo in repo_templates
                                          ]))

        output_stream.write('\n')

    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "List",
                                   config_params,
                                   output_stream,
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
              **vars
            ):
        output_stream.write("Searching for repositories in '{}'...".format(code_root))
        with StreamDecorator(output_stream).DoneManager(done_suffix='\n'):
            diff = _CalculateRepoDiff( code_root,
                                       repo_templates,
                                       vars,
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
            expected_branch_name = repo.branch if repo.branch else scm.DefaultBranch
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
                                   output_stream,
                                   Impl,
                                   prefix_args=[ ( "code_root", _NoDefault, CommandLine.DirectoryTypeInfo() ),
                                               ],
                                  )

# ---------------------------------------------------------------------------
def EnlistFunctionFactory( repo_templates,
                           config_params,
                           output_stream=sys.stdout,
                         ):
    repo_templates = _NormalizeRepoTemplates(repo_templates)
    
    potential_scms = SourceControlManagement.GetPotentialSCMs()

    # ---------------------------------------------------------------------------
    def Impl( code_root,
              scm='',
              remove_extra_repos=False,
              preserve_branches=False,
              flat=False,
              **vars
            ):
        scm = next(obj for obj in potential_scms if obj.Name == scm)
        
        output_stream.write("Searching for repositories in '{}'...".format(code_root))
        with StreamDecorator(output_stream).DoneManager(done_suffix='\n'):
            diff = _CalculateRepoDiff( code_root,
                                       repo_templates,
                                       vars,
                                     )

        branches_to_restore = OrderedDict()

        with StreamDecorator(output_stream).DoneManager(line_prefix='', done_prefix='\n', done_suffix='\n') as dm:
            
            # Update
            for index, repo in enumerate(diff.matches):
                current_branch_name = repo.scm.GetCurrentBranch(repo.path)
                branch_name = repo.branch or (current_branch_name if preserve_branches else repo.scm.DefaultBranch)
                
                title = "Updating '{}' [{}] ({} of {})...".format( repo.path,
                                                                   branch_name,
                                                                   index + 1,
                                                                   len(diff.matches),
                                                                 )
                dm.stream.write("\n{}\n{}\n".format(title, '=' * len(title)))
                with dm.stream.DoneManager() as update_dm:
                    if preserve_branches:
                        if current_branch_name != branch_name:
                            branches_to_restore[repo.path] = current_branch_name

                    # Note that some SCMs will only pull according to the currently set
                    # branch.
                    title = "Setting Branch ({})...".format(branch_name)
                    update_dm.stream.write("{}\n{}".format(title, '-' * len(title)))
                    with update_dm.stream.DoneManager(done_suffix='\n') as set_branch_dm:
                        set_branch_dm.result, output = repo.scm.SetBranch(repo.path, branch_name)
                        set_branch_dm.stream.write(output)

                    if repo.scm.IsDistributed:
                        title = "Pulling Changes..."
                        update_dm.stream.write("{}\n{}".format(title, '-' * len(title)))
                        with update_dm.stream.DoneManager(done_suffix='\n') as pull_dm:
                            pull_dm.result, output = repo.scm.Pull(repo.path)
                            pull_dm.stream.write(output)

                    title = "Updating to '{}'...".format(repo.scm.Tip)
                    update_dm.stream.write("{}\n{}".format(title, '-' * len(title)))
                    with update_dm.stream.DoneManager(done_suffix='\n') as this_update_dm:
                        this_update_dm.result, output = repo.scm.Update(repo.path, SourceControlManagement.EmptyUpdateMergeArg())
                        this_update_dm.stream.write(output)

                    title = "Updating Branch ({})...".format(branch_name)
                    update_dm.stream.write("{}\n{}".format(title, '-' * len(title)))
                    with update_dm.stream.DoneManager(done_suffix='\n') as set_branch_dm:
                        set_branch_dm.result, output = repo.scm.Update(repo.path, SourceControlManagement.BranchUpdateMergeArg(branch_name))
                        set_branch_dm.stream.write(output)

            # Remove any local repos that shouldn't be here
            if remove_extra_repos:
                for index, repo in enumerate(diff.local_only):
                    dm.stream.write("Removing '{}' ({} of {})...".format( repo.path,
                                                                          index + 1,
                                                                          len(diff.local_only),
                                                                        ))
                    with dm.stream.DoneManager() as this_dm:
                        shutil.rmtree(repo.path)

            # Clone
            for index, (uri, branch) in enumerate(diff.reference_only):
                name = uri[uri.rfind('/') + 1:]
                branch = branch or scm.DefaultBranch

                if flat:
                    output_dir = os.path.join(code_root, name)
                else:
                    output_dir = os.path.join(code_root, *name.split('_'))

                title = "Enlisting in '{}' ['{}'] -> '{}' ({} of {})...".format( uri,
                                                                                 branch,
                                                                                 output_dir,
                                                                                 index + 1,
                                                                                 len(diff.reference_only),
                                                                               )
                dm.stream.write("\n{}\n{}".format(title, '-' * len(title)))
                with dm.stream.DoneManager() as this_dm:
                    this_dm.result, output = scm.Clone(uri, output_dir, branch=branch)
                    this_dm.stream.write(output)

            # Resore any branches
            for index, (repo_path, branch_name) in enumerate(branches_to_restore.iteritems()):
                title = "Restoring branch '{}' in '{}' ({} of {})...".format( branch_name,
                                                                              repo_path,
                                                                              index + 1,
                                                                              len(branches_to_restore),
                                                                            )
                dm.stream.write("\n{}\n{}".format(title, '-' * len(title)))
                with dm.stream.DoneManager() as this_dm:
                    this_dm.result, output = scm.SetBranch(repo_path, branch_name)
                    this_dm.stream.write(output)

            return dm.result

    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "Enlist",
                                   config_params,
                                   output_stream,
                                   Impl,
                                   prefix_args=[ ( "code_root", _NoDefault, CommandLine.DirectoryTypeInfo() ),
                                                 ( "scm", '"{}"'.format(potential_scms[0].Name), CommandLine.EnumTypeInfo(values=[ scm.Name for scm in potential_scms ]) ),
                                               ],
                                   suffix_args=[ ( "remove_extra_repos", False ),
                                                 ( "preserve_branches", False ),
                                                 ( "flat", False ),
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
              **vars
            ):
        output_stream.write("Searching for repositories in '{}'...".format(code_root))
        with StreamDecorator(output_stream).DoneManager(done_suffix='\n'):
            diff = _CalculateRepoDiff( code_root,
                                       repo_templates,
                                       vars,
                                     )

        if not diff.matches:
            return 

        setup_environment_script = Shell.GetEnvironment().CreateScriptName(SourceRepositoryTools.SETUP_ENVIRONMENT_NAME)
                
        with StreamDecorator(output_stream).DoneManager(line_prefix='', done_prefix='\n', done_suffix='\n') as dm:
            for index, repo in enumerate(diff.matches):
                filename = os.path.join(repo.path, setup_environment_script)
                assert os.path.isfile(filename), filename

                title = "Running '{}' ({} of {})...".format(filename, index + 1, len(diff.matches))
                dm.stream.write("\n{}\n{}".format(title, '=' * len(title)))
                with dm.stream.DoneManager() as this_dm:
                    command_line = filename

                    if repo.setup_configurations:
                        command_line += " {}".format(' '.join([ '"/configuration={}"'.format(config) for config in repo.setup_configurations ]))

                    result = subprocess.Popen( command_line,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT,
                                               shell=True,
                                             )

                    this_dm.stream.write(result.stdout.read())
                    this_dm.result = result.wait() or 0

        return dm.result

    # ---------------------------------------------------------------------------
    
    return _DefineDynamicFunction( "Setup",
                                   config_params,
                                   output_stream,
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
                            output_stream,
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

    for k, v in config_params.iteritems():
        constraint_params[k] = CommandLine.StringTypeInfo()
        params[k] = '"{}"'.format(v)

    ApplyArgs(suffix_args)

    d = { "CommandLine" : CommandLine,
          "constraint_params" : constraint_params,
          "Impl" : impl_func,
          func_name : None,
        }

    exec textwrap.dedent(
        """\
        @CommandLine.EntryPoint()
        @CommandLine.FunctionConstraints(**constraint_params)
        def {name}({params}):
            return Impl({args})
        """).format( name=func_name,
                     params=', '.join([ "{}{}".format(k, '' if v == _NoDefault else "={}".format(v)) for k, v in params.iteritems() ]),
                     args=', '.join([ "{k}={k}".format(k=k) for k in params.iterkeys() ]),
                   ) in d

    return d[func_name]

# ---------------------------------------------------------------------------
def _NormalizeRepoTemplates(repo_templates):
    # Ensure that we only have 1 instance of each item
    lookup = OrderedDict()

    for index, repo_template in enumerate(repo_templates):
        if isinstance(repo_template, str):
            repo_templates[index] = NormalizeRepoTemplates(repo_template)[0]
            repo_template = repo_templates[index]

        if repo_template.uri in lookup and lookup[repo_template.uri].branch != branch:
            raise Exception("The repository '{}' has been requested more than once with different branches ({}, {})".format( repo_template.uri,
                                                                                                                             lookup[repo_template.uri].branch,
                                                                                                                             repo_template.branch,
                                                                                                                          ))

        lookup[repo_template.uri] = repo_template

    return repo_templates

# ---------------------------------------------------------------------------
def _CalculateRepoDiff( code_root,
                        repo_templates,
                        vars,
                      ):
    RepoInfo = NamedTuple("RepoInfo", "scm", "uri", "branch", "setup_configurations", path=None)

    matches = []
    local_only = []

    repo_uri_lookup = OrderedDict()
    
    for repo_template in repo_templates:
        uri = repo_template.uri.format(**vars)
        
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
                        reference_only=[ (uri, repo.branch) for uri, repo in repo_uri_lookup.itervalues() ],
                      )
