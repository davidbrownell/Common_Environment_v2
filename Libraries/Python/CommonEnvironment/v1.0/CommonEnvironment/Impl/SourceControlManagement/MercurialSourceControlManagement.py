# ---------------------------------------------------------------------------
# |  
# |  MercurialSourceControlManagement.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/27/2015 06:40:33 PM
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
import sys
import textwrap
import time

from collections import OrderedDict

from ...SourceControlManagement import DistributedSourceControlManagementBase, \
                                       EmptyUpdateMergeArg, \
                                       RevisionUpdateMergeArg, \
                                       DateUpdateMergeArg, \
                                       BranchUpdateMergeArg, \
                                       BranchAndDateUpdateMergeArg

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import six_plus

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# Note that functionality in this file require the following Mercurial extensions:
#       Mercurial Extension Name            Functionality
#       ----------------------------------  -------------------------------
#       purge                               Clean, Reset
#       strip                               Reset

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@staticderived
class MercurialSourceControlManagement(DistributedSourceControlManagementBase):
    
    Name                                    = "Mercurial"
    DefaultBranch                           = "default"
    Tip                                     = "tip"
    WorkingDirectories                      = [ ".hg", ]
    IgnoreFilename                          = ".hgignore"

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    
    # ---------------------------------------------------------------------------
    # |  SourceControlManagement Methods
    @staticmethod
    def Execute(repo_root, command, append_newline_to_output=True):
        command = command.replace("hg ", 'hg --cwd "{}" '.format(repo_root))

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
            result, output = cls.Execute(os.getcwd(), "hg version")
            is_available = result == 0 and "Mercurial Distributed SCM" in output

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
    @classmethod
    def IsRootDir(cls, repo_dir):
        return os.path.isdir(os.path.join(repo_dir, ".hg"))

    # ---------------------------------------------------------------------------
    @classmethod
    def Clone(cls, uri, output_dir, branch=None):
        clone_path, name = os.path.split(output_dir)

        if not os.path.isdir(clone_path):
            os.makedirs(clone_path)

        return cls.Execute(clone_path, 'hg clone{branch} "{uri}" "{name}"'.format( branch=' -b "{}"'.format(branch) if branch else '',
                                                                                   uri=uri,
                                                                                   name=name,
                                                                                 ))

    # ---------------------------------------------------------------------------
    @classmethod
    def Create(cls, output_dir):
        assert not os.path.isdir(output_dir), output_dir
        os.makedirs(output_dir)

        return cls.Execute(os.getcwd(), 'hg init "{}"'.format(output_dir))

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
                                      "hg root",
                                      append_newline_to_output=False,
                                    )
        assert result == 0, (result, output)
        
        cached_roots.add(output)

        return output

    # ---------------------------------------------------------------------------
    @classmethod
    def GetUniqueName(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg paths")
        assert result == 0, (result, output)

        regex = re.compile(r"{}\s*=\s*(?P<value>.+)".format(cls.DefaultBranch))

        for line in output.split('\n'):
            match = regex.match(line)
            if match:
                return match.group("value")

        # If here, we didn't find anything. Most of the time, this
        # is an indication that the repo is local; return the path.
        return os.path.realpath(repo_root)

    # ---------------------------------------------------------------------------
    @classmethod
    def Who(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg showconfig ui.username")
        assert result == 0, (result, output)

        return output.strip()

    # ---------------------------------------------------------------------------
    @classmethod
    def GetBranches(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg branches")
        assert result == 0, (result, output)

        regex = re.compile(r"(?P<name>\S+)\s*(?P<id>.+)")

        for match in regex.finditer(output):
            yield match.group("name")

    # ---------------------------------------------------------------------------
    @classmethod
    def GetCurrentBranch(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg branch")
        assert result == 0, (result, output)

        return output.strip()

    # ---------------------------------------------------------------------------
    @classmethod
    def GetMostRecentBranch(cls, repo_root):
        return cls._GetBranchAssociatedWithRevision(repo_root)

    # ---------------------------------------------------------------------------
    @classmethod
    def CreateBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'hg branch "{}"'.format(branch_name))

    # ---------------------------------------------------------------------------
    @classmethod
    def SetBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'hg update "{}"'.format(branch_name))

    # ---------------------------------------------------------------------------
    @classmethod
    def GetRevisionInfo(cls, repo_root, revision):
        result, output = cls.Execute(repo_root, 'hg log --rev "{}"'.format(revision))
        assert result == 0, (result, output)

        d = { "user" : None,
              "date" : None,
              "summary" : None,
            }

        for line in output.strip().split('\n'):
            for key in d.keys():
                if line.startswith(key):
                    assert d[key] == None
                    d[key] = line[len(key) + 1:].strip()
                    break

        for key, value in d.items():
            assert value, key

        d["files"] = cls.GetChangedFiles(repo_root, revision)

        return QuickObject(**d)

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

        commands = [ "hg update --clean",
                     "hg purge",
                   ]

        return cls.Execute(repo_root, " && ".join(commands))

    # ---------------------------------------------------------------------------
    @classmethod
    def HasWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg status")
        assert result == 0, (result, output)

        for line in output.split('\n'):
            line = line.strip()

            if line and not line.startswith('?'):
                return True
        
        return False

    # ---------------------------------------------------------------------------
    @classmethod
    def HasUntrackedWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg status")

        for line in output.split('\n'):
            line = line.lstrip()

            if line.startswith('?'):
                return True

        return False

    # ---------------------------------------------------------------------------
    @classmethod
    def CreatePatch( cls,
                     repo_root,
                     patch_filename,
                     start_change=None,
                     end_change=None,
                   ):
        if not start_change or not end_change:
            command_line = 'hg diff --git > "{}"'.format(patch_filename)
        else:
            command_line = 'hg export --git --rev "{start}:{end}" > "{filename}"'.format( start=start_change,
                                                                                          end=end_change,
                                                                                          filename=patch_filename,
                                                                                        )

        return cls.Execute(repo_root, command_line)

    # ---------------------------------------------------------------------------
    @classmethod
    def ApplyPatch(cls, repo_root, patch_filename, commit=False):
        return cls.Execute(repo_root, 'hg import{commit} "{filename}"'.format( commit=" --no-commit" if not commit else '',
                                                                               filename=patch_filename,
                                                                             ))

    # ---------------------------------------------------------------------------
    @classmethod
    def Commit(cls, repo_root, description, username=None):
        return cls.Execute( repo_root,
                            'hg commit --message "{desc}"{user}'.format( desc=description.replace('"', '\\"'),
                                                                         user=' --user "{}"'.format(username) if username else '',
                                                                       ),
                          )

    # ---------------------------------------------------------------------------
    @classmethod
    def Update(cls, repo_root, update_merge_arg):
        return cls.Execute(repo_root, 'hg update{}'.format(cls._UpdateMergeArgToCommandLine(repo_root, update_merge_arg)))

    # ---------------------------------------------------------------------------
    @classmethod
    def Merge(cls, repo_root, update_merge_arg):
        return cls.Execute(repo_root, 'hg merge{}'.format(cls._UpdateMergeArgToCommandLine(repo_root, update_merge_arg)))

    # ---------------------------------------------------------------------------
    @classmethod
    def GetRevisionsSinceLastMerge(cls, repo_root, dest_branch, source_update_merge_arg):
        source_branch = None
        additional_filters = []

        # ----------------------------------------------------------------------
        def GetDateOperator(arg):
            if arg is None or arg:
                return '>'

            return '<'

        # ----------------------------------------------------------------------

        if isinstance(source_update_merge_arg, EmptyUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)

        elif isinstance(source_update_merge_arg, RevisionUpdateMergeArg):
            source_branch = cls._GetBranchAssociatedWithRevision(repo_root, source_update_merge_arg.Revision)
            additional_filters.append("{}::".format(source_update_merge_arg.Revision))

        elif isinstance(source_update_merge_arg, BranchAndDateUpdateMergeArg):
            source_branch = source_update_merge_arg.Branch
            additional_filters.append("date('{}{}')".format( GetDateOperator(source_update_merge_arg.Greater),
                                                             StringSerialization.SerializeItem(DateTimeTypeInfo(), source_update_merge_arg.Date, microseconds=False),
                                                           ))

        elif isinstance(source_update_merge_arg, DateUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)
            additional_filters.append("date('{}{}')".format( GetDateOperator(source_update_merge_arg.Greater),
                                                             StringSerialization.SerializeItem(DateTimeTypeInfo(), source_update_merge_arg.Date, microseconds=False),
                                                           ))

        elif isinstance(source_update_merge_arg, BranchUpdateMergeArg):
            source_branch = source_update_merge_arg.Branch

        else:
            assert False, type(source_update_merge_arg)

        filter = "::{} and not ::{}".format(source_branch, dest_branch)
        if additional_filters:
            filter += " and {}".format(' and '.join(additional_filters))

        command_line = r'hg log --branch "{source_branch}" --rev "{filter}" --template "{rev}\n"' \
                            .format( source_branch=source_branch,
                                     filter=filter,
                                     rev="{rev}",
                                   )

        result, output = cls.Execute(repo_root, command_line)
        assert result == 0, (result, output)

        return [ line.strip() for line in output.split('\n') if line.strip() ]
    
    # ---------------------------------------------------------------------------
    @classmethod
    def GetChangedFiles(cls, repo_root, revision_or_revisions_or_none):
        command_line_template = 'hg status'
       
        if revision_or_revisions_or_none:
            revisions = revision_or_revisions_or_none if isinstance(revision_or_revisions_or_none, list) else [ revision_or_revisions_or_none, ]
            command_line_template += ' --change "{rev}"'
        else:
            revisions = [ None, ]

        filenames = []

        for revision in revisions:
            command_line = command_line_template.format(rev=revision)

            result, output = cls.Execute(repo_root, command_line)
            assert result == 0, (result, output)

            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                assert len(line) > 2 and line[1] == ' ' and line[2] != ' ', line
            
                filename = os.path.join(repo_root, line[2:])
                if filename not in filenames:
                    filenames.append(filename)

        return filenames

    # ---------------------------------------------------------------------------
    _EnumBlameInfo_regex                    = re.compile(r'^\s*(?P<revision>\d+):\s*(?P<line>.*)$')

    @classmethod
    def EnumBlameInfo(cls, repo_root, filename):
        result, output = cls.Execute(repo_root, 'hg blame "{}"'.format(filename))
        
        if result != 0:
            # Don't produce an error if we are looking at a file that has
            # been renamed/removed.
            if "no such file in" in output:
                return

            assert result == 0, (result, output)

        for index, line in enumerate(output.split('\n')):
            if not line:
                continue

            match = cls._EnumBlameInfo_regex.match(line)
            if not match:
                # Don't produce an error on a failure to enumerate binary files
                if line.endswith("binary file"):
                    return

                assert False, line

            yield index + 1, match.group("revision"), match.group("line")

    # ---------------------------------------------------------------------------
    # |  DistributedSourceControlManagement Methods
    
    @classmethod
    def Reset(cls, repo_root, no_prompt=False, no_backup=False):
        if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent(
            # <Wrong hanging indentation> pylint: disable = C0330
            """\
            This operation will revert your local repository to match the state of the remote repository.
                                                                
            THIS INCLUDES THE FOLLOWING:
               - Any working edits
               - Any files that have been added
               - Any committed local changes that have not been pushed to the remote repository
            """)):
            return 0, ''

        commands = [ 'hg update --clean',
                     'hg purge',
                     'hg strip{backup} "roots(outgoing())"'.format(backup=" --no-backup" if no_backup else ''),
                   ]

        empty_revision_set_notice = "abort: empty revision set"

        result, output = cls.Execute(repo_root, " && ".join(commands))
        if result != 0 and empty_revision_set_notice in output:
            result = 0
            output = output.replace(empty_revision_set_notice, '')

        return result, "{}\n".format(output.strip())

    # ---------------------------------------------------------------------------
    @classmethod
    def HasUpdateChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg summary")
        return result == 0 and output.find("update: (current)") == -1
        
    # ---------------------------------------------------------------------------
    @classmethod
    def HasLocalChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg outgoing")
        assert result == 0 or (result == 1 and "no changes found" in output), (result, output)

        return result == 0

    # ---------------------------------------------------------------------------
    @classmethod
    def GetLocalChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg summary --remote")
        assert result == 0, (result, output)
    
        regex = re.compile(r"remote:\s*(\(.+?)\)|(?P<changes>\d+) outgoing")
            
        match = regex.search(output)
        assert match, output
        
        changes = match.group("changes")
        if not changes:
            return []
        
        # Get the changes themselves
        result, output = cls.Execute(repo_root, r'hg log --limit {changes} --template "{node}\n"'.format( changes=changes,
                                                                                                          node="{node}",
                                                                                                        ))
        assert result == 0, (result, output)
        
        return [ line.strip() for line in output.split('\n') if line.strip() ]    

    # ---------------------------------------------------------------------------
    @classmethod
    def HasRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg incoming")
        assert result == 0 or (result == 1 and "no changes found" in output), (result, output)

        return result == 0

    # ---------------------------------------------------------------------------
    @classmethod
    def GetRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, r'hg incoming --template "node:{node}\n"')
        assert result == 0

        changes = []

        for line in output.split('\n'):
            if line.startswith("node:"):
                changes.append(line[len("node:"):].strip())

        return changes

    # ---------------------------------------------------------------------------
    @classmethod
    def Push(cls, repo_root, create_remote_branch=False):
        return cls.Execute(repo_root, "hg push{}".format(" --new-branch" if create_remote_branch else ''))

    # ---------------------------------------------------------------------------
    @classmethod
    def Pull(cls, repo_root, branch_or_branches=None):
        # In Mercurial, a pull gets all branches - no need to consider branch_or_branches
        result, output = cls.Execute(repo_root, "hg pull")
        if result != 0 and "no changes found" in output:
            result = 0

        return result, output

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @classmethod
    def _AddFilesImpl(cls, repo_root, filenames):
        return cls.Execute(repo_root, 'hg add {}'.format(' '.join([ '"{}"'.format(filename) for filename in filenames ])))

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetBranchAssociatedWithRevision(cls, repo_root, revision=None):
        command_line = 'hg log {revision} --template "{branch}"'.format( revision="--rev {}".format(revision) if revision else "-l 1",
                                                                         branch="{branch}",
                                                                       )

        result, output = cls.Execute(repo_root, command_line)
        assert result == 0, (result, output)

        return output.strip()

    # ---------------------------------------------------------------------------
    @classmethod
    def _UpdateMergeArgToString(cls, repo_root, arg):
        # ---------------------------------------------------------------------------
        def NormalizeRevision(revision):
            try:
                value = int(revision)
                if value >= 0:
                    return revision

            except ValueError:
                pass

            result, output = cls.Execute(repo_root, 'hg log --rev "{rev_num}" --template "{rev}"'.format( rev_num=revision,
                                                                                                          rev="{rev}",
                                                                                                        ))
            assert result == 0, (result, output)

            return output.strip()

        # ---------------------------------------------------------------------------
        def DateAndBranch(date, branch, operator):
            assert date

            if branch:
                def BranchGenerator():
                    yield branch
            else:
                def BranchGenerator():
                    for branch in [ cls.GetCurrentBranch(repo_root),
                                    cls.DefaultBranch,
                                  ]:
                        yield branch

            assert BranchGenerator

            if not operator:
                operator = '<'
            else:
                operator = '>'

            errors = OrderedDict()

            for branch in BranchGenerator():
                command_line = '''hg log --branch "{branch}" --rev "sort(date('{operator}{date}'), -date)" --limit 1 --template "{rev}"''' \
                                        .format( branch=branch,
                                                 operator=operator,
                                                 date=StringSerialization.SerializeItem(DateTimeTypeInfo(), date, microseconds=False),
                                                 rev="{rev}",
                                               )

                result, output = cls.Execute(repo_root, command_line)
                output = output.strip()

                if result == 0 and output:                    
                    return output

                errors[command_line] = output

            raise Exception("Revision not found ({branch}, {date})\n{errors}".format( branch=branch, 
                                                                                      date=date,
                                                                                      errors='\n\n'.join([ "{}\n{}".format(k, v) for k, v in errors.iteritems() ]),
                                                                                    ))

        # ---------------------------------------------------------------------------
        
        dispatch_map = { EmptyUpdateMergeArg :          lambda: "",
                         RevisionUpdateMergeArg :       lambda: NormalizeRevision(arg.Revision),
                         DateUpdateMergeArg :           lambda: DateAndBranch(arg.Date.replace(microsecond=0), None, arg.Greater),
                         BranchUpdateMergeArg :         lambda: DateAndBranch(DateTimeTypeInfo.Create(microseconds=False), arg.Branch, None),
                         BranchAndDateUpdateMergeArg :  lambda: DateAndBranch(arg.Date.replace(microsecond=0), arg.Branch, arg.Greater),
                       }

        assert type(arg) in dispatch_map, type(arg)
        return dispatch_map[type(arg)]()

    # ---------------------------------------------------------------------------
    @classmethod
    def _UpdateMergeArgToCommandLine(cls, repo_root, arg):
        revision = cls._UpdateMergeArgToString(repo_root, arg)
        if not revision:
            return ''

        if isinstance(arg, BranchUpdateMergeArg):
            return ' "{}"'.format(revision)

        return ' --rev "{}"'.format(revision)
