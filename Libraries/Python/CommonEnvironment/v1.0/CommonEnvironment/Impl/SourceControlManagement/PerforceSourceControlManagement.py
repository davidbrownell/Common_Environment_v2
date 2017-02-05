# ---------------------------------------------------------------------------
# |  
# |  PerforceSourceControlManagement.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/03/2015 05:51:21 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import os
import re
import subprocess
import sys
import textwrap

from collections import OrderedDict
from contextlib import contextmanager

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import *
from CommonEnvironment import Package
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import Shell

from ...SourceControlManagement import SourceControlManagementBase, \
                                       EmptyUpdateMergeArg, \
                                       RevisionUpdateMergeArg, \
                                       DateUpdateMergeArg, \
                                       BranchUpdateMergeArg, \
                                       BranchAndDateUpdateMergeArg

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

def PerforceSourceControlManagementFactory( raise_on_username_failure,
                                            username='',
                                            trunk_suffix='',
                                            trunk_name="trunk",
                                            branches_name="branches",
                                            tags_name="tags",
                                          ):
    username = username or os.getenv("P4USER")
    if not username and raise_on_username_failure:
        raise Exception("'username' must be provided or defined in the 'P4USER' environment variable.")

    trunk_suffix = trunk_suffix or os.getenv("P4TRUNKSUFFIX") or ''
    if trunk_suffix:
        # Ensure that the suffix starts with a '/' and does not end with a '/'
        if trunk_suffix[0] != '/':
            trunk_suffix = "/{}".format(trunk_suffix)
        if trunk_suffix[-1] == '/':
            trunk_suffix = trunk_suffix[:-1]
        
    # ---------------------------------------------------------------------------
    @staticderived
    class SCM(SourceControlManagementBase):
        
        # ---------------------------------------------------------------------------
        # |
        # |  Public Properties
        # |
        # ---------------------------------------------------------------------------
        Username                            = username
        TrunkSuffix                         = trunk_suffix
        TrunkName                           = trunk_name
        BranchesName                        = branches_name
        TagsName                            = tags_name
    
        Name                                = "Perforce"
        DefaultBranch                       = TrunkName
        Tip                                 = "T"
        WorkingDirectories                  = []
    
        # ---------------------------------------------------------------------------
        # |
        # |  Public Methods
        # |
        # ---------------------------------------------------------------------------
        @classmethod
        def IsAvailable(cls):
            is_available = getattr(cls, "_cached_is_available", None)
            if is_available == None:
                if not cls.Username:
                    is_available = False
                else:
                    result, output = cls.Execute(os.getcwd(), "p4 info")
                    is_available = result == 0
    
                setattr(cls, "_cached_is_available", is_available)
    
            return is_available
            
        # ---------------------------------------------------------------------------
        @classmethod
        def IsActive(cls, repo_dir):
            try:
                cls._GetClient(repo_dir)
                return True
            except:
                return False
    
        # ---------------------------------------------------------------------------
        @classmethod
        def Clone(cls, uri, output_dir, branch=None):
            raise Exception("Cloning is non-trivial in Perforce; please create a connection followed by a workspace.")
    
        # ---------------------------------------------------------------------------
        @classmethod
        def Create(cls, output_dir):
            raise Exception("Perforce does not support local repositories.")
            
        # ---------------------------------------------------------------------------
        @classmethod
        def GetRoot(cls, repo_dir):
            return cls._GetClient(repo_dir).RepoRoot
            
        # ---------------------------------------------------------------------------
        @classmethod
        def GetUniqueName(cls, repo_root):
            return cls._GetClient(repo_root).RepoName
            
        # ---------------------------------------------------------------------------
        @classmethod
        def Who(cls, repo_root):
            client = cls._GetClient(repo_root)
    
            result, output = client.Execute('p4 client -o "{}"'.format(client.RepoName))
            assert result == 0, (result, output)
            
            owner = None
            
            for line in output.split('\n'):
                if line.startswith("Owner:"):
                    owner = line[len("Owner:"):].strip()
                    break
                    
            assert owner, output
            return owner
    
        # ---------------------------------------------------------------------------
        @classmethod
        def GetBranches(cls, repo_root):
            client = cls._GetClient(repo_root)
    
            # ---------------------------------------------------------------------------
            def TrunkExtractor(output):
                assert output
                return [ cls.TrunkName, ]
    
            # ---------------------------------------------------------------------------
            def BranchExtractor(output):
                branches = []
    
                for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                    branch_name = cls._ExtractBranchName(line, branch_prefix=cls.BranchesName)
                    assert branch_name, line
    
                    branches.append(branch_name)
    
                return branches
    
            # ---------------------------------------------------------------------------
            
            branches = []
    
            for name, extractor in [ ( cls.TrunkName, TrunkExtractor ),
                                     ( cls.BranchesName, BranchExtractor ),
                                   ]:
                result, output = client.Execute('p4 dirs "{}/{}/*"'.format(client.GetMappingRoot(), name))
                if result == 0 and output.find("no such file(s)") == -1:
                    branches += extractor(output)
    
            return branches
    
        # ---------------------------------------------------------------------------
        @classmethod
        def GetCurrentBranch(cls, repo_root):
            client = cls._GetClient(repo_root)
    
            potential_branches = OrderedDict()
    
            for key, value in client.GetFileMappings().iteritems():
                branch_name = cls._ExtractBranchName(key)
                if branch_name:
                    potential_branches[branch_name] = (key, value)
    
            if not potential_branches:
                return cls.DefaultBranch
    
            if len(potential_branches) > 1:
                raise Exception("The name of the current branch was ambigous; please ensure that only one branch is mapped into the current view. Candidates are {}.".format(', '.join([ "'{}' ({}, {})".format(k, *v) for k, v in potential_branches.iteritems() ])))
    
            return potential_branches.keys()[0]
    
        # ---------------------------------------------------------------------------
        @classmethod
        def GetMostRecentBranch(cls, repo_root):
            client = cls._GetClient(repo_root)
    
            result, output = client.Execute('p4 changes -m 1 "{}/..."'.format(client.GetMappingRoot()))
            assert result == 0, (result, output)
    
            match = re.search(r"Change (?P<revision>\d+).+", output)
            assert match, output
    
            info = client.GetRevisionInfo(match.group("revision"), apply_mappings=False)
            
            assert info.files
            branch = cls._ExtractBranchName(info.files[0])
            assert branch
    
            return branch
    
        # ---------------------------------------------------------------------------
        @classmethod
        def CreateBranch(cls, repo_root, branch_name):
            raise Exception("Branching is a manual process within Perforce")
    
        # ---------------------------------------------------------------------------
        @classmethod
        def SetBranch(cls, repo_root, branch_name):
            client = cls._GetClient(repo_root)
    
            # Get the client template
            result, output = client.Execute('p4 client -o "{}"'.format(client.RepoName))
            assert result == 0, (result, output)
    
            # Modify the client template
            
            # ---------------------------------------------------------------------------
            def PopulateViews(match):
                items = [ item.strip() for item in match.group("content").split('\n') if item.strip() ]
                assert items
    
                regex = re.compile(r"(?P<pre>.+/)((?:{branches_name}/[^/]+)|{trunk_name}{trunk_suffix})/(?P<post>.+)".format( branches_name=re.escape(cls.BranchesName),
                                                                                                                              trunk_name=re.escape(cls.TrunkName),
                                                                                                                              trunk_suffix=re.escape(cls.TrunkSuffix),
                                                                                                                            ))
                
                replacement = "{}/".format(cls._GetBranchName(branch_name))

                items = [ regex.sub( lambda match: "{}{}{}".format(match.group("pre"), replacement, match.group("post")),
                                     item,
                                   )
                          for item in items 
                        ]
    
                return "View:\n{}\n".format('\n'.join([ "\t{}".format(item) for item in items ]))
    
            # ---------------------------------------------------------------------------
            
            output = re.sub( r"View:[ \t]*\r?\n(?P<content>(?:\t[^\n]+\r?\n)+)",
                             PopulateViews,
                             output,
                             flags=re.DOTALL | re.MULTILINE,
                           )
    
            # Write the template to a temporary file and apply it
            temp_filename = Shell.GetEnvironment().CreateTempFilename()
    
            with open(temp_filename, 'w') as f:
                f.write(output)
    
            # Apply the client template
            result, output = client.Execute('p4 client -i < "{}"'.format(temp_filename))
            assert result == 0, (result, output)
    
            # Sync the changes
            return client.Execute('p4 sync -s -q')
                
        # ---------------------------------------------------------------------------
        @classmethod
        def GetRevisionInfo(cls, repo_root, revision):
            return cls._GetClient(repo_root).GetRevisionInfo(revision)
    
        # ---------------------------------------------------------------------------
        @classmethod
        def Clean(cls, repo_root, no_prompt=False):
            if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent(
                # <Wrong hanging indentation> pylint: disable = C0330
                """\
                This operation will revert any working changes.
                          
                THIS INCLUDES THE FOLLOWING:
                   - Any working edits
                   - Any files that have been added
                """)):
                return 0, ''
    
            return cls._GetClient(repo_root).Execute('p4 revert -w //...')
    
        # ---------------------------------------------------------------------------
        @classmethod
        def HasWorkingChanges(cls, repo_root):
            result, output = cls._GetClient(repo_root).Execute('p4 opened')
            assert result == 0, (result, output)
    
            return output.find("Files(s) not opened") == -1
    
        # ---------------------------------------------------------------------------
        @classmethod
        def HasUntrackedWorkingChanges(cls, repo_root):
            # Without the ability to ignore files, there is likely to be
            # many files in the repository that aren't tracked.
            return None
    
        # ---------------------------------------------------------------------------
        @classmethod
        def CreatePatch( cls,
                         repo_root,
                         patch_filename,
                         start_change=None,
                         end_change=None,
                       ):
            raise NotImplementedError("TODO: Not implemented")
    
        # ---------------------------------------------------------------------------
        @classmethod
        def ApplyPatch(cls, repo_root, patch_filename, commit=False):
            raise NotImplementedError("TODO: Not implemented")
    
        # ---------------------------------------------------------------------------
        @classmethod
        def Commit(cls, repo_root, description, username=None):
            return cls._GetClient(repo_root).Execute('p4 submit -d "{}"'.format(description))
    
        # ---------------------------------------------------------------------------
        @classmethod
        def Update(cls, repo_root, update_merge_arg, force=False):
            return cls._GetClient(repo_root).Execute('p4 sync{force} {arg}'.format( force=" -f" if force else '',
                                                                                    arg=cls._UpdateMergeArgToString(update_merge_arg),
                                                                                  ))
    
        # ---------------------------------------------------------------------------
        @classmethod
        def Merge(cls, repo_root, update_merge_arg):
            client = cls._GetClient(repo_root)

            source_branch = None
            source_arg = ''

            if isinstance(update_merge_arg, (EmptyUpdateMergeArg, DateUpdateMergeArg)):
                raise Exception("A source branch must be specified")
            elif isinstance(update_merge_arg, RevisionUpdateMergeArg):
                info = client.GetRevisionInfo(update_merge_arg.Revision, apply_mappings=False)
                
                assert info.files
                branch = cls._ExtractBranchName(info.files[0])
                assert branch

                source_branch = branch
            elif isinstance(update_merge_arg, BranchUpdateMergeArg):
                source_branch = update_merge_arg.Branch
            elif isinstance(update_merge_arg, BranchAndDateUpdateMergeArg):
                source_branch = update_merge_arg.Branch
                source_arg = "@{}".format(update_merge_arg.Date)
            else:
                assert False, update_merge_arg

            return client.Execute('p4 integrate "{mapping_root}/{source_branch}/...{source_arg}" "{mapping_root}/{this_branch}/..."'.format(
                        mapping_root=cliennt.GetMappingRoot(),
                        source_branch=cls._GetBranchName(source_branch),
                        source_arg=source_arg,
                        this_branch=cls._GetBranchName(cls.GetCurrentBranch(repo_root)),
                   ))
    
        # ---------------------------------------------------------------------------
        @classmethod
        def GetRevisionsSinceLastMerge(cls, repo_root, dest_branch, source_update_merge_arg):
            if isinstance(source_update_merge_arg, (BranchUpdateMergeArg, BranchAndDateUpdateMergeArg)):
                raise Exception("No support for filtering changes across branches")

            client = cls._GetClient(repo_root)
    
            result, output = client.Execute('p4 interchanges "{mapping_root}/{this_branch}/...{this_arg}" "{mapping_root}/{dest_branch}/..."'.format(
                                mapping_root=client.GetMappingRoot(),
                                this_branch=cls._GetBranchName(cls.GetCurrentBranch(repo_root)),
                                this_arg=cls._UpdateMergeArgToString(source_update_merge_arg),
                                dest_branch=cls._GetBranchName(dest_branch),
                             ))
    
            assert result == 0, (result, output)
    
            revisions = []
    
            regex = re.compile("Change (?P<revision>\d+) ")
            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                match = regex.match(line)
                assert match, line
    
                revisions.append(match.group("revision"))
    
            return revisions
    
        # ---------------------------------------------------------------------------
        @classmethod
        def GetChangedFiles(cls, repo_root, revision_or_revisions_or_none):
            assert revision_or_revisions_or_none, "Getting local changes isn't supported yet"
            revisions = revision_or_revisions if isinstance(revision_or_revisions, list) else [ revision_or_revisions, ]
    
            client = cls._GetClient(repo_root)
    
            files = []
            for revision in revisions:
                result = client.GetRevisionInfo(revision)
                files += result.files
    
            return files
    
        # ---------------------------------------------------------------------------
        @classmethod
        def EnumBlameInfo(cls, repo_root, filename):
            client = cls._GetClient(repo_root)
    
            result, output = client.Execute('p4 annotate -I -q "{}"'.format(filename))
            if result != 0:
                raise Exception(output)
    
            regex = re.compile(r"(?P<revision>\d+): (?P<line>.*)")
    
            for index, line in enumerate(output.strip().replace('\r\n', '\n').split('\n')):
                match = regex.match(line)
                assert match, line
    
                yield index + 1, match.group("revision"), match.group("line")
    
        # ---------------------------------------------------------------------------
        # |
        # |  Private Methods
        # |
        # ---------------------------------------------------------------------------
        @classmethod
        def _AddFilesImpl(cls, repo_root, filenames):
            client = cls._GetClient(repo_root)
    
            environment = Shell.GetEnvironment()
    
            temp_filename = environment.CreateTempFilename(environment.ScriptExtension)
            with open(temp_filename, 'w') as f:
                f.write('\n'.join([ 'p4 add "{}"'.format(filename) for filename in filenames ]))
    
            with CallOnExit(lambda: os.remove(temp_filename)):
                environment.MakeFileExecutable(temp_filename)
    
                return client.Execute(temp_filename)
    
        # ---------------------------------------------------------------------------
        @classmethod
        def _GetClient(cls, repo_root):
            if not hasattr(cls, "_clients"):
                cls._clients = {}
    
            if repo_root not in cls._clients:
                cls._clients[repo_root] = _Client(cls.Username, repo_root, cls)
    
            assert repo_root in cls._clients
            return cls._clients[repo_root]
    
        # ---------------------------------------------------------------------------
        @classmethod
        def _ExtractBranchName(cls, s, branch_prefix=None):
            s = s.split('/')
    
            if branch_prefix == None or branch_prefix == cls.TrunkName:
                if cls.TrunkName in s:
                    return cls.TrunkName
                
            if branch_prefix == None or branch_prefix == cls.BranchesName:
                for index, item in enumerate(s):
                    if item == cls.BranchesName:
                        assert index != len(s) - 1, s
                        return s[index + 1]
    
        # ---------------------------------------------------------------------------
        @classmethod
        def _GetBranchName(cls, name):
            if name == cls.TrunkName:
                return "{}{}".format(cls.TrunkName, cls.TrunkSuffix)

            return "{}/{}".format(cls.BranchesName, name)

        # ---------------------------------------------------------------------------
        @staticmethod
        def _UpdateMergeArgToString(arg):
            # ---------------------------------------------------------------------------
            def Revision(rev):
                return "...@{}".format(rev)
    
            # ---------------------------------------------------------------------------
            def Date(date):
                return "@{}".format(date)
    
            # ---------------------------------------------------------------------------
            def Branch():
                raise Exception("Perforce does not provide the functionality to sync to a branch that is not mapped in the current view.")
    
            # ---------------------------------------------------------------------------
            
            dispatch_map = { EmptyUpdateMergeArg :          lambda: "",
                             RevisionUpdateMergeArg :       lambda: Revision(arg.Revision),
                             DateUpdateMergeArg :           lambda: Date(arg.Date),
                             BranchUpdateMergeArg :         lambda: Branch(),
                             BranchAndDateUpdateMergeArg :  lambda: Branch(),
                           }
    
            assert type(arg) in dispatch_map, type(arg)
            return dispatch_map[type(arg)]()

    # ---------------------------------------------------------------------------
    
    return SCM

# ---------------------------------------------------------------------------
PerforceSourceControlManagement = PerforceSourceControlManagementFactory( raise_on_username_failure=False,
                                                                        )

# ---------------------------------------------------------------------------
# |
# |  Private Types
# |
# ---------------------------------------------------------------------------
class _Client(object):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    def __init__( self, 
                  username,
                  repo_dir,
                  p4scm,
                  only_local_workspaces=True,
                  filter_func=None,         # def Func(name, dir) -> Bool
                ):
        self._p4scm                         = p4scm
        self._username                      = username
        
        # Propulated below
        self._execute_functor               = None
        
        self.RepoName                       = None
        self.RepoRoot                       = None
        
        # The following values are initialized on demand in other methods
        self._mappings                      = None
        self._mapping_root                  = None

        # Get the repo name and root
        environment = Shell.GetEnvironment()
        
        if not repo_dir.endswith(os.path.sep):
            repo_dir += os.path.sep
            
        if not environment.HasCaseSensitiveFileSystem:
            repo_dir = repo_dir.lower()
            
        # ---------------------------------------------------------------------------
        def EnumWorkspaces():
            if only_local_workspaces:
                # Get the host name (which isn't workspace-specific)
                host_name = None

                result, output = p4scm.Execute(repo_dir, 'p4 info')
                assert result == 0, (result, output)

                for line in output.split('\n'):
                    if line.startswith("Client host:"):
                        host_name = line[len("Client host:"):].strip()
                        break

                assert host_name, output

                # ---------------------------------------------------------------------------
                def LocalFilterFunc(workspace_name):
                    result, output = p4scm.Execute(repo_dir, 'p4 client -o "{}"'.format(workspace_name))
                    assert result == 0, (result, output)

                    this_host_name = None

                    for line in output.split('\n'):
                        if line.startswith("Host:"):
                            this_host_name = line[len("Host:"):].strip()
                            break

                    return this_host_name == host_name

                # ---------------------------------------------------------------------------
                
            else:
                # ---------------------------------------------------------------------------
                def LocalFilterFunc(_):
                    return True

                # ---------------------------------------------------------------------------
            
            result, output = p4scm.Execute(repo_dir, 'p4 clients -u "{}"'.format(self._username))
            assert result == 0, (result, output)
                
            workspace_regex = re.compile(textwrap.dedent(
               r"""(?#
                Prefix                  )Client\s+(?#
                Name                    )(?P<name>\S+)\s+(?#
                Date                    )(?P<date>\d{4}\/\d{2}\/\d{2})\s+(?#
                Root                    )root\s+(?#
                Dir                     )(?P<dir>.+?)\s+(?#
                Desc                    )'(?P<desc>.+?)'\s*(?#
                )"""))

            workspaces = OrderedDict()

            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                match = workspace_regex.match(line)
                assert match, line

                name = match.group("name")
                directory = match.group("dir")
            
                if not directory.endswith(os.path.sep):
                    directory += os.path.sep

                if LocalFilterFunc(name) and (not filter_func or filter_func(name, directory)):
                    yield name, directory

        # ---------------------------------------------------------------------------
        
        for name, directory in EnumWorkspaces():
            comparison_dir = directory if environment.HasCaseSensitiveFileSystem else directory.lower()
            if repo_dir.startswith(comparison_dir):
                self.RepoName = name
                self.RepoRoot = directory

                break
                
        if not self.RepoName or not self.RepoRoot:
            raise Exception("Unable to map a client to '{}'".format(repo_dir))

        # TODO: This execute stuff is wonky. Originally, it was designed to
        #       set environment variables for use with p4, but it turns out
        #       that the info can be set on the command line. If I ever use
        #       Perforce again in the future, remove this stuff and just do
        #       a straight Execute without the strange work arounds.

        # ----------------------------------------------------------------------
        def Execute(repo_root, command, append_newline_to_output=True):
            if not os.path.isdir(repo_root):
                return -1, "'{}' is not a valid dir".format(repo_root)
    
            current_dir = os.getcwd()
    
            os.chdir(repo_root)
            with CallOnExit(lambda: os.chdir(current_dir)):
                result = subprocess.Popen( command,
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           env=os.environ,
                                         )
                content = result.stdout.read().strip()
                result = result.wait() or 0
    
                if append_newline_to_output and content:
                    content += '\n'
    
                return result, content
    
        # ----------------------------------------------------------------------
            
        self._execute_functor               = Execute
        
    # ---------------------------------------------------------------------------
    _GetFileMappings_regex = None 

    def GetFileMappings(self):
        if self._mappings == None:
            result, output = self.Execute('p4 where')
            assert result == 0, (result, output)

            if self._GetFileMappings_regex == None:
                self._GetFileMappings_regex = re.compile(textwrap.dedent(
                   r"""(?#
                    Minus           )(?P<minus>-)?(?#
                    Repo            )(?P<repo>.+?)/...\s+(?#
                    Unique Name     )(?P<unique_name>.+?)/...\s+(?#
                    File System     )(?P<file_system>.+){sep}...\s*(?#
                    )""").format(sep=re.escape(os.path.sep)))

            data = []

            for line in output.strip().split('\n'):
                match = self._GetFileMappings_regex.match(line)
                assert match, line

                if match.group("minus"):
                    continue

                data.append((match.group("repo"), match.group("unique_name"), match.group("file_system")))

            # Order from most- to least-specific
            data.sort(key=lambda i: len(i[0]), reverse=True)

            self._mappings = OrderedDict([ (i[0], i[2] ) for i in data ])

        assert self._mappings != None
        return self._mappings

    # ---------------------------------------------------------------------------
    def GetMappingRoot(self):
        if self._mapping_root == None:
            mappings = self.GetFileMappings()

            for key in mappings.iterkeys():
                key_parts = key.split('/')
                for index, part in enumerate(key_parts):
                    if part in [ self._p4scm.TrunkName, 
                                 self._p4scm.BranchesName, 
                                 self._p4scm.TagsName, 
                               ]:
                        self._mapping_root = '/'.join(key_parts[:index])
                        break

                if self._mapping_root:
                    break

        assert self._mapping_root != None
        return self._mapping_root

    # ---------------------------------------------------------------------------
    _GetRevisionInfo_describe_regex = None
    _GetRevisionInfo_file_regex = None

    def GetRevisionInfo(self, revision, apply_mappings=True):
        result, output = self.Execute('p4 describe -s "{}"'.format(revision))
        assert result == 0, (result, output)

        if self._GetRevisionInfo_describe_regex == None:
            self._GetRevisionInfo_describe_regex = re.compile(textwrap.dedent(
               r"""(?#
                                )Change\s+(?#
                Id              )(?P<id>\d+)\s+(?#
                                )by\s+(?#
                Username        )(?P<username>\S+)@(?#
                Workspace       )(?P<workspace>\S+)\s+(?#
                                )on\s+(?#
                Date            )(?P<date>(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2}))\s+(?#
                Time            )(?P<time>(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}))\s*(?#
                Description     )\n^(?P<desc>.+?)$\n(?#
                                )Affected files \.\.\.\s*(?#
                Files           )\n^(?P<files>.+)$\n(?#
                )"""),  
                              re.DOTALL | re.MULTILINE,
                            )

            self._GetRevisionInfo_file_regex = re.compile(textwrap.dedent(
               r"""(?#
                Prefix          )\s*...\s+(?#
                Depo Filename   )(?P<name>.+?)(?#
                Version         )#(?P<version>\d+)\s+(?#
                Type            )(?P<type>\S+)(?#
                )"""))

        match = self._GetRevisionInfo_describe_regex.match(output)
        assert match, output

        # ---------------------------------------------------------------------------
        def GetFiles(content):
            if apply_mappings:
                mappings = self.GetFileMappings()

                # ---------------------------------------------------------------------------
                def ApplyMapping(depo_filename):
                    for k, v in mappings.iteritems():
                        if depo_filename.startswith(k):
                            return "{}{}".format(v, depo_filename[len(k):].replace('/', os.path.sep))

                    return depo_filename

                # ---------------------------------------------------------------------------
                
            else:
                # ---------------------------------------------------------------------------
                def ApplyMapping(depo_filename):
                    return depo_filename

                # ---------------------------------------------------------------------------
                
            files = []

            for line in [ line.strip() for line in content.split('\n') if line.strip() ]:
                match = self._GetRevisionInfo_file_regex.match(line)
                assert match, line

                name = match.group("name")
                name = ApplyMapping(name)

                files.append(name)

            return files

        # ---------------------------------------------------------------------------
        
        return QuickObject( revision=match.group("id"),
                            user=match.group("username"),
                            date=datetime.datetime( int(match.group("year")),
                                                    int(match.group("month")),
                                                    int(match.group("day")),
                                                    int(match.group("hour")),
                                                    int(match.group("minute")),
                                                    int(match.group("second")),
                                                  ),
                            summary=textwrap.dedent(match.group("desc").strip()),
                            files=GetFiles(match.group("files").strip()),
                          )

    # ---------------------------------------------------------------------------
    def Execute(self, command_line):
        # TODO: Update this so it doesn't set the environment for all threads
        os.environ["P4CLIENT"] = self.RepoName
        os.environ["P4USER"] = self._username
        
        # ----------------------------------------------------------------------
        def RemoveEnvironmentValues():
            del os.environ["P4CLIENT"]
            del os.environ["P4USER"]

        # ----------------------------------------------------------------------
        
        with CallOnExit(RemoveEnvironmentValues):
            # This is strange - Perforce will look at the environment variable PWD before checking for the
            # working directory, meaning changing into the directory will not have any effect unless PWD changes 
            # too. Capture the current PWD value, change it to our working directory, and then store it when
            # the process completes.
            original_pwd_value = None
            
            if "PWD" in os.environ:
                original_pwd_value = os.environ["PWD"]
                del os.environ["PWD"]
            
            results = self._execute_functor(self.RepoRoot, command_line)
        
            if original_pwd_value:
                os.environ["PWD"] = original_pwd_value

        return results
