# ----------------------------------------------------------------------
# |  
# |  GitSourceControlManagement.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-03-29 07:51:07
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import re
import sys
import textwrap

from collections import OrderedDict

import six

from ...SourceControlManagement import DistributedSourceControlManagementBase, \
                                       EmptyUpdateMergeArg, \
                                       RevisionUpdateMergeArg, \
                                       DateUpdateMergeArg, \
                                       BranchUpdateMergeArg, \
                                       BranchAndDateUpdateMergeArg

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import RegularExpression
from CommonEnvironment import six_plus

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@staticderived
class GitSourceControlManagement(DistributedSourceControlManagementBase):

    Name                                    = "Git"
    DefaultBranch                           = "master"
    Tip                                     = "head"
    WorkingDirectories                      = [ ".git", ]
    IgnoreFilename                          = ".gitignore"

    DetachedHeadPseudoBranchName            = "__DetachedHeadPseudoBranchName_%(Index)d_%(BranchName)s__"
    _DetachedHeadPseudoBranchName_regex     = RegularExpression.TemplateStringToRegex(DetachedHeadPseudoBranchName)

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    
    # ----------------------------------------------------------------------
    # |  SourceControlManagement Methods
    @staticmethod
    def Execute(repo_root, command, append_newline_to_output=True):
        command = command.replace("git ", 'git -C "{}" '.format(repo_root))

        result, content = Process.Execute( command,
                                           environment=os.environ,
                                         )

        content = content.strip()
        
        if append_newline_to_output and content:
            content += '\n'

        return result, content
    
    # ----------------------------------------------------------------------
    @classmethod
    def IsAvailable(cls):
        is_available = getattr(cls, "_cached_is_available", None)
        if is_available == None:
            result, output = cls.Execute(os.getcwd(), "git")
            is_available = output.find("usage: git") != -1

            setattr(cls, "_cached_is_available", is_available)

        return is_available

    # ---------------------------------------------------------------------------
    @classmethod
    def IsActive(cls, repo_dir):
        if not hasattr(cls, "_cached_is_active"):
            setattr(cls, "_cached_is_active", set())

        cached = getattr(cls, "_cached_is_active")

        for k in cached:
            if repo_dir.startswith(k):
                return True

        try:
            result = os.path.isdir(cls.GetRoot(repo_dir))
            
            # Note that we are only caching positive results. This is to ensure
            # that we walk into repositories associated with subdirs when provided
            # with a root that isn't a repository (caching a failure on a root dir
            # would indicate failure for all subdirs as well).
            if result:
                cached.add(repo_dir)

        except:
            result = False

        return result

    # ---------------------------------------------------------------------------
    @staticmethod
    def IsRootDir(repo_dir):
        return os.path.isdir(os.path.join(repo_dir, ".git"))

    # ---------------------------------------------------------------------------
    @classmethod
    def Clone(cls, uri, output_dir, branch=None):
        clone_path, name = os.path.split(output_dir)

        if not os.path.isdir(clone_path):
            os.makedirs(clone_path)

        return cls.Execute( clone_path,
                            'git clone{branch} {uri} "{name}"' \
                                    .format( branch=' -b "{}"'.format(branch) if branch else '',
                                             uri=uri,
                                             name=name,
                                           ),
                          )

    # ---------------------------------------------------------------------------
    @classmethod
    def Create(cls, output_dir):
        assert not os.path.isdir(output_dir), output_dir
        os.makedirs(output_dir)

        return cls.Execute(output_dir, "git init")

    # ---------------------------------------------------------------------------
    @classmethod
    def GetRoot(cls, repo_dir):
        if not hasattr(cls, "_cached_roots"):
            setattr(cls, "_cached_roots", set())

        cached_roots = getattr(cls, "_cached_roots")

        for k in cached_roots:
            if repo_dir.startswith(k):
                return k

        result, output = cls.Execute( repo_dir, 
                                      "git rev-parse --show-toplevel",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)

        cached_roots.add(output)

        return output

    # ---------------------------------------------------------------------------
    _GetUniqueName_regex                    = re.compile(r"origin\s+(?P<url>.+?)\s+\(fetch\)")

    @classmethod
    def GetUniqueName(cls, repo_root):
        result, output = cls.Execute(repo_root, "git remote -v")
        assert result == 0, (result, output)

        for line in output.split('\n'):
            match = cls._GetUniqueName_regex.match(line)
            if match:
                return match.group("url")

        # If here, we didn't find anything. Most of the time, this
        # is an indication that the repo is local; return the path.
        return os.path.realpath(repo_root)

    # ---------------------------------------------------------------------------
    @classmethod
    def Who(cls, repo_root):
        # ----------------------------------------------------------------------
        def GetValue(name):
            result, output = cls.Execute(repo_root, "git config {}".format(name))
            assert result == 0, (result, output)

            return output.strip()

        # ----------------------------------------------------------------------
        
        return "{} <{}>".format( GetValue("user.name"),
                                 GetValue("user.email"),
                               )

    # ---------------------------------------------------------------------------
    _GetBranches_regex                      = re.compile(r"^\*?\s*\[(origin/)?(?P<name>\S+?)\]\s+.+?")

    @classmethod
    def GetBranches(cls, repo_root):
        result, output = cls.Execute( repo_root, 
                                      "git show-branch --list --all",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)

        branches = set()

        for line in output.split('\n'):
            match = cls._GetBranches_regex.match(line)
            if not match:
                continue
        
            branch = match.group("name")
            if branch not in branches:
                branches.add(branch)
                yield branch

    # ---------------------------------------------------------------------------
    _GetCurrentBranch_regex                 = re.compile(r"\s*\*\s+(?P<name>.+)")

    @classmethod
    def GetCurrentBranch(cls, repo_root):
        result, output = cls.Execute( repo_root, 
                                      "git branch --no-color",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        if output:
            for line in output.split('\n'):
                match = cls._GetCurrentBranch_regex.match(line)
                if match:
                    return match.group("name")

        return cls.DefaultBranch

    # ---------------------------------------------------------------------------
    @classmethod
    def GetCurrentNormalizedBranch(cls, repo_root):
        branch = cls.GetCurrentBranch(repo_root)

        match = cls._DetachedHeadPseudoBranchName_regex.match(branch)
        if match:
            return match.group("BranchName")
        
        return branch

    # ---------------------------------------------------------------------------
    @classmethod
    def GetMostRecentBranch(cls, repo_root):
        result, output = cls.Execute( repo_root, 
                                      "git for-each-ref --sort=-committerdate --format=%(refname)",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        for line in output.split('\n'):
            parts = line.split('/')
            
            if parts[1] == "remotes" and \
               parts[2] == "origin":
                    return parts[3]
                    
        assert False, output

    # ---------------------------------------------------------------------------
    @classmethod
    def CreateBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'git branch "{name}" && git checkout "{name}"'.format(name=branch_name))

    # ---------------------------------------------------------------------------
    @classmethod
    def SetBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'git checkout "{}"'.format(branch_name))

    # ---------------------------------------------------------------------------
    @classmethod
    def GetRevisionInfo(cls, repo_root, revision):
        # Note the spaces to work around issues with git
        format = " %aN <%ae> %n %cd %n %s"
        
        result, output = cls.Execute( repo_root, 
                                      'git --no-pager show -s --format="{}" {}'.format(format, revision),
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        lines = output.split('\n')
        assert len(lines) >= 3, (len(lines), output)
        
        return QuickObject( user=lines[0].lstrip(),
                            date=lines[1].lstrip(),
                            summary=lines[2].lstrip(),
                          )

    # ---------------------------------------------------------------------------
    @classmethod
    def Clean(cls, repo_root, no_prompt=False):
        if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent("""\
            This operation will revert any local changes.
            
            THIS INCLUDES THE FOLLOWING:
               - Any working changes
               - Any files that have been added
            """)):
            return 0, ''

        commands = [ "git reset --hard",
                     "git clean -df",
                   ]

        return cls.Execute(repo_root, " && ".join(commands))

    # ---------------------------------------------------------------------------
    @classmethod
    def HasWorkingChanges(cls, repo_root):
        result, output = cls.Execute( repo_root, 
                                      "git --no-pager diff --name-only",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        return bool(output)

    # ---------------------------------------------------------------------------
    @classmethod
    def HasUntrackedWorkingChanges(cls, repo_root):
        result, output = cls.Execute( repo_root,
                                      "git ls-files --others --exclude-standard",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)

        return bool(output)

    # ---------------------------------------------------------------------------
    @classmethod
    def CreatePatch( cls, 
                     repo_root,
                     patch_filename,
                     start_change=None,
                     end_change=None,
                   ):
        if not start_change or not end_change:
            return cls.Execute(repo_root, 'git diff -g > "{}"'.format(patch_filename))

        return cls.Execute(repo_root, 'git diff -g {} {} > "{}"'.format( start_change,
                                                                         end_change,
                                                                         patch_filename,
                                                                       ))

    # ---------------------------------------------------------------------------
    @classmethod
    def ApplyPatch(cls, repo_root, patch_filename, commit=False):
        # Git does not support "no_commit"
        assert not no_commit

        return cls.Execute(repo_root, 'git apply "{}"'.format(patch_filename))

    # ---------------------------------------------------------------------------
    _Commit_regex                           = re.compile(r"(?P<username>.+?)\s+\<(?P<email>.+?)\>")

    @classmethod
    def Commit(cls, repo_root, description, username=None):
        # Git is particular about username format - massage it into the right
        # format if necessary.
        if username:
            match = cls._Commit_regex.match(username)
            if not match:
                username = "{} <noreply@Generator.com>".format(username)
                
        return cls.Execute( repo_root, 
                            'git commit -a --allow-empty -m "{desc}"{author}' \
                               .format( desc=description.replace('"', '\\"'),
                                        author=' --author="{}"'.format(username) if username else '',
                                      ),
                          )

    # ---------------------------------------------------------------------------
    @classmethod
    def Update(cls, repo_root, update_merge_arg):
        branch = cls.GetCurrentBranch(repo_root)

        commands = [ 'git merge --ff-only "origin/{}"'.format(branch),
                   ]

        if isinstance(update_merge_arg, EmptyUpdateMergeArg):
            pass
        elif isinstance(update_merge_arg, BranchUpdateMergeArg):
            commands.insert(0, 'git checkout "{}"'.format(update_merge_arg.Branch))
        else:
            revision = cls._UpdateMergeArgToString(repo_root, update_merge_arg)

            # Updating to a specific revision within Git is interesting, as one will find
            # themselves in a "DETACHED HEAD" state. While this makes a lot of sense from
            # a commit perspective, it doesn't make as much sense from a reading perspective
            # (especially in scenarios where it is necessary to derive the branch name from the
            # current state, as will be the case during Reset). To work around this, Update to
            # a new branch that is cleverly named in a way that can be parsed by commands that
            # need this sort of information.
            existing_branch_names = set(cls.GetBranches(repo_root))

            index = 0
            while True:
                potential_branch_name = cls.DetachedHeadPseudoBranchName.format( Index=index,
                                                                                 BranchName=branch,
                                                                               )

                if potential_branch_name not in existing_branch_names:
                    break

                index += 1

            commands.append('git checkout {} -b "{}"'.format(revision, potential_branch_name))

        return cls.Execute(repo_root, " && ".join(commands))

    # ---------------------------------------------------------------------------
    @classmethod
    def Merge(cls, repo_root, update_merge_arg):
        return cls.Execute(repo_root, "git merge --no-commit --no-ff {}".format(cls._UpdateMergeArgToString(repo_dir, update_merge_arg)))


    # ---------------------------------------------------------------------------
    @classmethod
    def GetRevisionsSinceLastMerge(cls, repo_root, dest_branch, source_update_merge_arg):
        # Git is really screwed up. After a 30 minute search, I couldn't find a way to
        # specify a branch and beginning revision in a single command. Therefore, I am
        # resorting to do it manually.

        source_branch = None
        additional_filters = []
        post_decorator_func = None

        # ----------------------------------------------------------------------
        def GetDateOperator(arg):
            if arg is None or arg:
                return "since"

            return "until"

        # ----------------------------------------------------------------------

        if isinstance(source_update_merge_arg, EmptyUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)

        elif isinstance(source_update_merge_arg, RevisionUpdateMergeArg):
            source_branch = cls._GetBranchAssociateWithRevision(source_update_merge_arg.Revision)

            # ----------------------------------------------------------------------
            def AfterRevisionDecorator(changes):
                starting_index = None

                for index, change in enumerate(changes):
                    if change == source_update_merge_arg.Revision:
                        starting_index = index          # Start after the found item
                        break

                if starting_index is None:
                    return []

                return changes[starting_index:]

            # ----------------------------------------------------------------------

            post_decorator_func = AfterRevisionDecorator

        elif isinstance(source_update_merge_arg, BranchUpdateMergeArg):
            source_branch = source_update_merge_arg.Branch

        elif isinstance(source_update_merge_arg, BranchAndDateUpdateMergeArg):
            source_branch = source_update_merge_arg.Branch
            additional_filters.append('--{}="{}"'.format( GetDateOperator(source_update_merge_arg.Greater),
                                                          StringSerialization.SerializeItem(DateTimeTypeInfo(), source_update_merge_arg.Date),
                                                        ))

        elif isinstance(source_update_merge_arg, DateUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)
            additional_filters.append('--{}="{}"'.format( GetDateOperator(source_update_merge_arg.Greater),
                                                          StringSerialization.SerializeItem(DateTimeTypeInfo(), source_update_merge_arg.Date),
                                                        ))

        else:
            assert False, type(source_update_merge_arg)

        command_line = r'git --no-pager log "{source_branch}" --not "{dest_branch}" --format=%H --no-merges{additional_filters}' \
                            .format( source_branch=source_branch,
                                     dest_branch=dest_branch,
                                     additional_filters='' if not additional_filters else " {}".format(' '.join(additional_filters)),
                                   )

        result, output = cls.Execute(repo_root, command_line)
        assert result == 0, (result, output)

        changes = [ line.strip() for line in output.split('\n') if line.strip() ]

        if post_decorator_func is not None:
            changes = post_decorator_func(changes)

        return changes

    # ---------------------------------------------------------------------------
    _GetChangedFiles_regex                  = None

    @classmethod
    def GetChangedFiles(cls, repo_root, revision_or_revisions_or_none):
        if revision_or_revisions_or_none == None:
            result, output = cls.Execute( repo_root,
                                          "git status --short",
                                          append_newline_to_output=False,
                                        )
            assert result == 0, (result, output)

            if cls._GetChangedFiles_regex == None:
                cls._GetChangedFiles_regex = re.compile(r'^\S\s+"(?P<filename>.+)"$')

            filenames = []

            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                match = cls._GetChangedFiles_regex.match(line)
                assert match

                filenames.append(os.path.join(repo_root, match.group("filename")))

            return filenames

        else:
            revisions = revision_or_revisions_or_none if isinstance(revision_or_revisions_or_none, list) else [ revision_or_revisions_or_none, ]
            command_line_template = "git diff-tree --no-commit-id --name-only -r {}"

            filenames = []

            for revision in revisions:
                command_line = command_line_template.format(revision)

                result, output = cls.Execute( repo_root,
                                              command_line,
                                              append_newline_to_output=False,
                                            )
                assert result == 0, (result, output)

                for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                    filename = os.path.join(repo_root, line)

                    if filename not in filenames:
                        filenames.append(filename)

            return filenames

    # ---------------------------------------------------------------------------
    _EnumBlameInfo_regex                    = re.compile(r"^(?P<revision>\S+) (?P<line_number>\d+)\)(?: (?P<line>.*))?$")

    @classmethod
    def EnumBlameInfo(cls, repo_root, filename):
        result, output = cls.Execute( repo_root, 
                                      'git blame -s "{}"'.format(filename),
                                      append_newline_to_output=False,
                                    )
        
        if result != 0:
            # Don't produce an error if we are looking at a file that has
            # been renamed/removed.
            if "No such file or directory" in output:
                return

        for line in output.split('\n'):
            match = cls._EnumBlameInfo_regex.match(line)
            assert match, line

            yield int(match.group("line_number")), match.group("revision"), match.group("line")

    # ---------------------------------------------------------------------------
    # |  DistributedSourceControlManagement Methods
    
    @classmethod
    def Reset(cls, repo_root, no_prompt=False, no_backup=False):
        if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent(
            """\
            This operation will revert your local repository to match the state of the remote repository.
            
            THIS INCLUDES THE FOLLOWING:
               - Any working changes
               - Any files that have been added
               - Any committed local changes that have not been pushed to the remote repository
            """)):
            return 0, ''

        commands = []
        
        # See if we are looking at a Detached head pseudo branch. If so, extract
        # the actual branch name and switch to that before running the other commands.
        branch = cls.GetCurrentBranch(repo_root)
        
        match = cls._DetachedHeadPseudoBranchName_regex.match(branch)
        if match:
            branch = match.group("BranchName")
            commands.append('git checkout "{}"'.format(branch))
        
        # Remove any of the pseudo branches that have been created
        for potential_delete_branch in cls.GetBranches(repo_root):
            if cls._DetachedHeadPseudoBranchName_regex.match(potential_delete_branch):
                commands.append('git branch -D "{}"'.format(potential_delete_branch))
                
        commands.extend([ 'git reset --hard "origin/{}"'.format(branch),
                          "git clean -df",
                        ])

        return cls.Execute(repo_root, " && ".join(commands))

    # ---------------------------------------------------------------------------
    @classmethod
    def HasUpdateChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git status -uno")
        assert result == 0, (result, output)
        
        return "Your branch is behind" in output or "have diverged" in output

    # ---------------------------------------------------------------------------
    @classmethod
    def HasLocalChanges(cls, repo_root):
        result, output = cls.Execute( repo_root, 
                                      "git --no-pager log --branches --not --remotes",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        return bool(output)

    # ---------------------------------------------------------------------------
    @classmethod
    def GetLocalChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git remote update")
        assert result == 0, (result, output)
        
        result, output = cls.Execute( repo_root,
                                      'git --no-pager log "origin/{}..HEAD" --format=%H'.format(cls.GetCurrentBranch(repo_root)),
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        return [ line.strip() for line in output.split('\n') if line.strip() ]

    # ---------------------------------------------------------------------------
    @classmethod
    def HasRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git remote update")
        assert result == 0, (result, output)
        
        return cls.HasUpdateChanges(repo_root)

    # ---------------------------------------------------------------------------
    @classmethod
    def GetRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git remote update")
        assert result == 0, (result, output)

        result, output = cls.Execute( repo_root,
                                      'git --no-pager log "HEAD..origin/{}" --format=%H'.format(cls.GetCurrentBranch(repo_root)),
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        return [ line.strip() for line in output.split('\n') if line.strip() ]

    # ---------------------------------------------------------------------------
    @classmethod
    def Push(cls, repo_root, create_remote_branch=False):
        commands = [ "git push",
                     "git push --tags",
                   ]

        if create_remote_branch:
            commands[0] += ' --set-upstream origin "{}"'.format(cls.GetCurrentBranch(repo_root))

        return cls.Execute(repo_root, " && ".join(commands))

    # ---------------------------------------------------------------------------
    @classmethod
    def Pull(cls, repo_root, branch_or_branches=None):
        commands = []

        if isinstance(branch_or_branches, six.string_types):
            branch_or_branches = [ branch_or_branches, ]

        existing_branches = set(cls.GetBranches(repo_root))

        for branch_name in (branch_or_branches or []):
            if branch_name not in existing_branches:
                commands.append('git checkout -b "{name}" "origin/{name}"'.format(name=branch_name))
                
        commands += [ "git fetch --all",
                      "git fetch --all --tags",
                    ]

        return cls.Execute(repo_root, " && ".join(commands))
    
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _AddFilesImpl(cls, repo_root, filenames):
        return cls.Execute(repo_root, 'git add {}'.format(' '.join([ '"{}"'.format(filename) for filename in filenames ])))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _GetBranchAssociatedWithRevision(cls, repo_root, revision):
        result, output = cls.Execute( repo_root,
                                      'git branch --contains {}'.format(revision),
                                    )
        assert result == 0, (result, output)

        output = output.strip()
        if output.startswith("* "):
            output = output[len("* "):]

        return output

    # ----------------------------------------------------------------------
    @classmethod
    def _UpdateMergeArgToString(cls, repo_root, arg):

        # ----------------------------------------------------------------------
        def NormalizeRevision(revision):
            result, output = cls.Execute( repo_root, 
                                          "git --no-pager log {} -n 1 -format=%H".format(revision),
                                          append_newline_to_output=False,
                                        )
            assert result == 0, (result, output)

            return output

        # ----------------------------------------------------------------------
        def DateAndBranch(date, branch, operator):
            assert date

            if branch:
                # ----------------------------------------------------------------------
                def BranchGenerator():
                    yield branch

                # ----------------------------------------------------------------------
            else:
                # ----------------------------------------------------------------------
                def BranchGenerator():
                    for branch in [ cls.GetCurrentBranch(repo_root),
                                    cls.DefaultBranch,
                                  ]:
                        yield branch

                # ----------------------------------------------------------------------
                
            assert BranchGenerator

            if not operator:
                operator = "until"
            else:
                operator = "since"

            for branch in BranchGenerator():
                result, output = cls.Execute( repo_root, 
                                              'git --no-pager log "--branches=*{}" --{}={} -n 1 --format=%H'.format(branch, operator, date),
                                              append_newline_to_output=False,
                                            )

                if result == 0 and output:
                    return output

            assert False, "Revision not found"

        # ----------------------------------------------------------------------
        
        dispatch_map = { EmptyUpdateMergeArg :          lambda: "",
                         RevisionUpdateMergeArg :       lambda: NormalizeRevision(arg.Revision),
                         DateUpdateMergeArg :           lambda: DateAndBranch(arg.Date, None, arg.Greater),
                         BranchUpdateMergeArg :         lambda: arg.Branch,
                         BranchAndDateUpdateMergeArg :  lambda: DateAndBranch(arg.Date, arg.Branch, arg.Greater),
                       }

        assert type(arg) in dispatch_map, type(arg)
        return dispatch_map[type(arg)]()
