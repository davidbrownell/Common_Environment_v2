# ---------------------------------------------------------------------------
# |  
# |  SourceControlManagement.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/26/2015 07:15:21 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import textwrap

from .CallOnExit import CallOnExit
from . import Enum
from . import FileSystem
from .Interface import Interface, abstractmethod, abstractproperty
from .QuickObject import QuickObject

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class UpdateMergeArg(object):
    """\
    Argument passed to an update and/or merge command
    """

    Operation = Enum.Create("Update", "Merge", "Other")

    # ---------------------------------------------------------------------------
    @staticmethod
    def FromCommandLine( revision=None,
                         branch=None,
                         date=None,
                       ):
        if revision:
            return RevisionUpdateMergeArg(revision)

        if branch and date:
            return BranchAndDateUpdateMergeArg(branch, date)

        if branch:
            return BranchUpdateMergeArg(branch)

        if date:
            return DateUpdateMergeArg(branch)

        return EmptyUpdateMergeArg()

# ---------------------------------------------------------------------------
class EmptyUpdateMergeArg(UpdateMergeArg):
    """\
    By default, update to the most recent change on the current branch.
    """
    def __init__(self):
        pass

    def __str__(self):
        return "<SCM-specific tip>"

# ---------------------------------------------------------------------------
class RevisionUpdateMergeArg(UpdateMergeArg):
    """\
    Change branches based on the branch associated with the revision.
    """
    def __init__(self, revision):
        self.Revision = revision

    def __str__(self):
        return self.Revision

# ---------------------------------------------------------------------------
class DateUpdateMergeArg(UpdateMergeArg):
    """\
    Change nearest to the date on any branch.
    """
    def __init__(self, date):
        self.Date = date

    def __str__(self):
        return self.Date

# ---------------------------------------------------------------------------
class BranchUpdateMergeArg(UpdateMergeArg):
    """\
    Most recent change on the specified branch.
    """
    def __init__(self, branch):
        self.Branch = branch

    def __str__(self):
        return self.Branch

# ---------------------------------------------------------------------------
class BranchAndDateUpdateMergeArg(UpdateMergeArg):
    """\
    Change nearest to the date on the specified branch.
    """
    def __init__(self, branch, date):
        self.Branch = branch
        self.Date = date

    def __str__(self):
        return "{} ({})".format(self.Branch, self.Date)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class SourceControlManagementBase(Interface):

    # By convention, all actions return (return_code, output) for all actions.
    # An action is any method without a prefix of "Is", "Has", or "Get".

    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def DefaultBranch(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Tip(self):
        raise Exception("Abstract property")

    @abstractproperty
    def WorkingDirectories(self):
        raise Exception("Abstract property")

    IsDistributed                           = False

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsAvailable():
        """Returns True if the SCM is available on the current machine"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsActive(repo_dir):
        """Returns True if the SCM is active in the current repo dir"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def IsRootDir(cls, repo_dir):
        return cls.IsAvailable() and cls.IsActive(repo_dir) and cls.GetRoot(repo_dir) == repo_dir

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Clone(uri, output_dir, branch=None):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Create(output_dir):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRoot(repo_dir):
        """\
        Returns the root directory of the repo associated with the provided directory using
        conventions specific to the SCM.
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetUniqueName(repo_root):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Who(repo_root):
        """Gets the username associated with the specified repo."""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetBranches(repo_root):
        """Gets all local branches"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetCurrentBranch(repo_root):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def GetCurrentNormalizedBranch(cls, repo_root):
        """\
        Some SCMs (such as Git) need to do wonky things to ensure that branches
        stay consistent (e.g. avoid a detached head state). Those wonky things may
        require branch renames that are not exposed to the end user. This method
        will "undo" those changes if necessary.
        """
        return cls.GetCurrentBranch(repo_root)

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetMostRecentBranch(repo_root):
        """Returns the branch associated with the most recent change"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def CreateBranch(repo_root, branch_name):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def SetBranch(repo_root, branch_name):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def SetBranchOrDefault(cls, repo_root, branch_name):
        """Sets the working branch to branch_name if branch_name is a valid branch"""
        return cls.SetBranch( repo_root,
                              branch_name if branch_name in cls.GetBranches(repo_root) else cls.DefaultBranch,
                            )

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRevisionInfo(repo_root, revision):
        """\
        Returns an object that contains information about a specific revision. At the
        very least, the object  will contain the attributes:
            - user
            - date
            - summary
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def AddFiles( cls, 
                  repo_root, 
                  file_filenames_or_recurse_flag,
                  functor=None,                         # def Func(fullpath) -> Bool
                ):
        """\
        Addes the file or files provided, or will search for new files in the 
        current dir (if the flag is set to False) or recursively (if the flag is 
        set to True).
        """
        if isinstance(file_filenames_or_recurse_flag, bool):
            if file_filenames_or_recurse_flag:
                # ---------------------------------------------------------------------------
                def GetFiles():
                    return FileSystem.WalkFiles( repo_root,
                                                 traverse_exclude_dir_names=cls.WorkingDirectories,
                                               )
                # ---------------------------------------------------------------------------
            else:
                # ---------------------------------------------------------------------------
                def GetFiles():
                    for item in os.listdir(repo_root):
                        fullpath = os.path.join(repo_root, item)
                        if os.path.isfile(fullpath):
                            yield fullpath

                # ---------------------------------------------------------------------------
                
            filenames = []

            for filename in GetFiles():
                if not functor or functor(filename):
                    filenames.append(filename)

        elif isinstance(file_filenames_or_recurse_flag, str):
            filenames = [ file_filenames_or_recurse_flag, ]

        else:
            filenames = file_filenames_or_recurse_flag

        for filename in filenames:
            if not os.path.isfile(filename):
                raise Exception("'{}' is not a valid filename".format(filename))

        return cls._AddFilesImpl(repo_root, filenames)

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Clean(repo_root, no_prompt=False):
        """Ensures that the repo is in a clean state (no working changes)"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasWorkingChanges(repo_root):
        """Are there changes to files tracked by the repo."""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasUntrackedWorkingChanges(repo_root):
        """Are there changes to files that are not tracked by the repo."""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def GetChangeStatus(cls, repo_root):
        return QuickObject( untracked=cls.HasUntrackedWorkingChanges(repo_root),
                            working=cls.HasWorkingChanges(repo_root),
                          )

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def CreatePatch( repo_root,
                     patch_filename,
                     start_change=None,
                     end_change=None,
                   ):
        # Local changes will be used if start_= and end_change are None
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def ApplyPatch(repo_root, patch_filename, commit=False):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Commit(repo_root, description, username=None):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Update(repo_root, update_merge_arg):
        raise Exception("Abstract Method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Merge(repo_root, update_merge_arg):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRevisionsSinceLastMerge(repo_root, dest_branch, source_update_merge_arg):
        """\
        Returns a list of all revisions between the last merge to the dest_branch
        and the given arg.
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetChangedFiles(repo_root, revision_or_revisions_or_none):
        """\
        Get a list of all files that have changed as part of the specified revision(s).
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def EnumBlameInfo(repo_root, filename):
        """\
        Generates (line, revision, text) for each line in the specified file.
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def AreYouSurePrompt(prompt):
        result = raw_input("{}\nEnter 'y' to continue or anything else to exit: ".format(prompt)).strip() == 'y'
        sys.stdout.write("\n")

        return result

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _AddFilesImpl(repo_root, filenames):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
class DistributedSourceControlManagementBase(SourceControlManagementBase):

    IsDistributed                           = True

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Reset(repo_root, no_prompt=False, no_backup=False):
        """Resets the repo to the remote state, erasing any unpushed (but committed) changes."""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasUpdateChanges(repo_root):
        """Are there changes that have been pulled but have yet to be updated."""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasLocalChanges(repo_root):
        """Are there changes yet to be pushed"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetLocalChanges(repo_root):
        """Returns a list of changes that have yet to be pushed"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasRemoteChanges(repo_root):
        """Are there changes to be pulled"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRemoteChanges(repo_root):
        """Returns a list of changes that have yet to be pulled"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @classmethod
    def GetChangeStatus(cls, repo_root):
        return QuickObject( untracked=cls.HasUntrackedWorkingChanges(repo_root),
                            working=cls.HasWorkingChanges(repo_root),
                            local=cls.HasLocalChanges(repo_root),
                            remote=cls.HasRemoteChanges(repo_root),
                            update=cls.HasUpdateChanges(repo_root),
                            branch=cls.GetMostRecentBranch(repo_root),
                          )

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Push(repo_root):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Pull(repo_root, branch_or_branches=None):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
# |
# |  Methods
# |
# ---------------------------------------------------------------------------
def GetPotentialSCMs():
    from .Impl.SourceControlManagement.MercurialSourceControlManagement import MercurialSourceControlManagement
    from .Impl.SourceControlManagement.PerforceSourceControlManagement import PerforceSourceControlManagement

    return [ MercurialSourceControlManagement,
             PerforceSourceControlManagement,
           ]

# ---------------------------------------------------------------------------
def GetSCM(repo_root, throw_on_error=True):
    available = []

    potential = GetPotentialSCMs()

    for scm in potential:
        if scm.IsAvailable():
            available.append(scm)
            if scm.IsActive(repo_root):
                return scm

    if not throw_on_error:
        return

    raise Exception(textwrap.dedent(
        """\
        No SCMs are active for '{repo_root}'.

        Available SCMs are:
        {available}

        Potential SCMs are:
        {potential}
        """).format( repo_root=repo_root,
                     available="    NONE" if not available else '\n'.join([ "    - {}".format(scm.Name) for scm in available ]),
                     potential="    NONE" if not potential else '\n'.join([ "    - {}".format(scm.Name) for scm in potential ]),
                   ))
    
# ---------------------------------------------------------------------------
def EnumSCMDirectories(root):
    assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
    sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
    with CallOnExit(lambda: sys.path.pop(0)):
        import SourceRepositoryTools

    scms = GetPotentialSCMs()

    for root, directories, _ in os.walk(root):
        for scm in scms:
            if scm.IsRootDir(root):
                yield scm, root
                directories[:] = []
                continue

        if SourceRepositoryTools.GENERATED_DIRECTORY_NAME in directories:
            directories.erase(SourceRepositoryTools.GENERATED_DIRECTORY_NAME)