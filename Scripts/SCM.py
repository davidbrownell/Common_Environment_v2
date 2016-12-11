# ---------------------------------------------------------------------------
# |  
# |  SCM.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/05/2015 10:02:02 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Tools for use with SourceControlManagement.
"""

import os
import re
import sys
import textwrap

from collections import OrderedDict
from StringIO import StringIO

import inflect

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import SourceControlManagement as SCMMod
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

_SCMTypeInfo = CommandLine.EnumTypeInfo([ scm.Name for scm in SCMMod.GetPotentialSCMs() ])
_SCMOptionalTypeInfo = CommandLine.EnumTypeInfo(_SCMTypeInfo.Values, arity='?')

inflect_engine = inflect.engine()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def CommandLineSuffix():
    return textwrap.dedent(
        """
            The SCM will be auto-detected if not specified. If specified, it can be one 
            of the following values:
        
        {values}

        """).format( values='\n'.join([ "        - {}".format(scm_name) for scm_name in _SCMTypeInfo.Values ]),
                   )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Info( directory=None,
          output_stream=sys.stdout,
        ):
    directory = directory or os.getcwd()

    col_widths = [ 60, 12, 9, ]
    template = "{name:<%d}  {is_available:<%d}  {is_active:<%d}\n" % tuple(col_widths)

    output_stream.write(template.format( name="Name",
                                         is_available="Is Available",
                                         is_active="Is Active",
                                       ))
    output_stream.write(template.format( name='-' * col_widths[0],
                                         is_available='-' * col_widths[1],
                                         is_active='-' * col_widths[2],
                                       ))

    for scm in SCMMod.GetPotentialSCMs():
        is_available = scm.IsAvailable()

        output_stream.write(template.format( name=scm.Name,
                                             is_available="True" if is_available else "False",
                                             is_active="True" if is_available and scm.IsActive(directory) else "False",
                                           ))

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMTypeInfo,
                                  uri=CommandLine.StringTypeInfo(),
                                  output_directory=CommandLine.StringTypeInfo(),
                                  branch=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def Clone( scm,
           uri,
           output_directory,
           branch=None,
           output_stream=sys.stdout,
         ):
    scm, _ = _GetSCMAndDir(scm, None)
    return CommandLine.DisplayOutput(*scm.Clone(uri, output_directory, branch or ''), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMTypeInfo,
                                  output_directory=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def Create( scm,
            output_directory,
            output_stream=sys.stdout,
          ):
    scm, _ = _GetSCMAndDir(scm, None)
    return CommandLine.DisplayOutput(*scm.Create(output_directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetRoot( scm=None,
             directory=None,
             output_stream=sys.stdout,
           ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetRoot(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetUniqueName( scm=None,
                   directory=None,
                   output_stream=sys.stdout,
                 ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetUniqueName(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Who( scm=None,
         directory=None,
         output_stream=sys.stdout,
       ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.Who(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetBranches( scm=None,
                 directory=None,
                 output_stream=sys.stdout,
               ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetBranches(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetCurrentBranch( scm=None,
                      directory=None,
                      output_stream=sys.stdout,
                    ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetCurrentBranch(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetCurrentNormalizedBranch( scm=None,
                                directory=None,
                                output_stream=sys.stdout,
                              ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetCurrentNormalizedBranch(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetMostRecentBranch( scm=None,
                         directory=None,
                         output_stream=sys.stdout,
                       ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetMostRecentBranch(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( branch=CommandLine.StringTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def CreateBranch( branch,
                  scm=None,
                  directory=None,
                  output_stream=sys.stdout,
                ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.CreateBranch(directory, branch), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( branch=CommandLine.StringTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def SetBranch( branch,
               scm=None,
               directory=None,
               output_stream=sys.stdout,
             ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.SetBranch(directory, branch), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( branch=CommandLine.StringTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def SetBranchOrDefault( branch,
                        scm=None,
                        directory=None,
                        output_stream=sys.stdout,
                      ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.SetBranchOrDefault(directory, branch), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( revision=CommandLine.StringTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetRevisionInfo( revision,
                     scm=None,
                     directory=None,
                     output_stream=sys.stdout,
                   ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetRevisionInfo(directory, revision), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( file=CommandLine.FilenameTypeInfo(arity='*'),
                                  recurse=CommandLine.BoolTypeInfo(arity='?'),
                                  include_re=CommandLine.StringTypeInfo(arity='*'),
                                  exclude_re=CommandLine.StringTypeInfo(arity='*'),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def AddFiles( file=None,
              recurse=None,
              include_re=None,
              exclude_re=None,
              scm=None,
              directory=None,
              output_stream=sys.stdout,
            ):
    if recurse == None and (include_re or exclude_re):
        recurse = False

    if file != [] and recurse != None:
        raise CommandLine.UsageException("'file' or 'recurse' arguments may be provied, but not both at the same time")

    if file == [] and recurse == None:
        raise CommandLine.UsageException("'file' or 'recurse' must be provided.")

    if recurse != None and (include_re or exclude_re):
        include_re = [ re.compile(ire) for ire in (include_re or []) ]
        exclude_re = [ re.compile(ere) for ere in (exclude_re or []) ]

        # ---------------------------------------------------------------------------
        def Functor(fullpath):
            return ( (not exclude_re or not any(ere.match(fullpath) for ere in exclude_re)) and
                     (not include_re or any(ire.match(fullpath) for ire in include_re))
                   )

        # ---------------------------------------------------------------------------
    else:
        # ---------------------------------------------------------------------------
        def Functor(_):
            return True
        # ---------------------------------------------------------------------------
        
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.AddFiles(directory, file or recurse, functor=Functor), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Clean( scm=None,
           directory=None,
           no_prompt=False,
           output_stream=sys.stdout,
         ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.Clean(directory, no_prompt=no_prompt), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def HasWorkingChanges( scm=None,
                       directory=None,
                       output_stream=sys.stdout,
                     ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.HasWorkingChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def HasUntrackedWorkingChanges( scm=None,
                                directory=None,
                                output_stream=sys.stdout,
                              ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.HasUntrackedWorkingChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetChangeStatus( scm=None,
                     directory=None,
                     output_stream=sys.stdout,
                   ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetChangeStatus(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( patch_filename=CommandLine.StringTypeInfo(),
                                  start_change=CommandLine.StringTypeInfo(arity='?'),
                                  end_change=CommandLine.StringTypeInfo(arity='?'),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def CreatePatch( patch_filename,
                 start_change=None,
                 end_change=None,
                 scm=None,
                 directory=None,
                 output_stream=sys.stdout,
               ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.CreatePatch(directory, patch_filename, start_change=start_change, end_change=end_change), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( patch_filename=CommandLine.FilenameTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def ApplyPatch( patch_filename,
                commit=False,
                scm=None,
                directory=None,
                output_stream=sys.stdout,
              ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.ApplyPatch(directory, patch_filename, commit=commit), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( description=CommandLine.StringTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Commit( description,
            scm=None,
            directory=None,
            output_stream=sys.stdout,
          ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.Commit(directory, description), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( revision=CommandLine.StringTypeInfo(arity='?'),
                                  branch=CommandLine.StringTypeInfo(arity='?'),
                                  date=CommandLine.DateTimeTypeInfo(arity='?'),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Update( revision=None,
            branch=None,
            date=None,
            scm=None,
            directory=None,
            output_stream=sys.stdout,
          ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.Update(directory, SCMMod.UpdateMergeArg.FromCommandLine(revision, branch, date)), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( revision=CommandLine.StringTypeInfo(arity='?'),
                                  branch=CommandLine.StringTypeInfo(arity='?'),
                                  date=CommandLine.DateTimeTypeInfo(arity='?'),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Merge( revision=None,
           branch=None,
           date=None,
           scm=None,
           directory=None,
           output_stream=sys.stdout,
         ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(*scm.Merge(directory, SCMMod.UpdateMergeArg.FromCommandLine(revision, branch, date)), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( dest_branch=CommandLine.StringTypeInfo(),
                                  source_revision=CommandLine.StringTypeInfo(arity='?'),
                                  source_branch=CommandLine.StringTypeInfo(arity='?'),
                                  source_date=CommandLine.DateTimeTypeInfo(arity='?'),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetRevisionsSinceLastMerge( dest_branch,
                                source_revision=None,
                                source_branch=None,
                                source_date=None,
                                scm=None,
                                directory=None,
                                output_stream=sys.stdout,
                              ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetRevisionsSinceLastMerge(directory, dest_branch, SCMMod.UpdateMergeArg.FromCommandLine(source_revision, source_branch, source_date)), output_stream=output_stream)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( revision=CommandLine.StringTypeInfo(arity='?'),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetChangedFiles( revision=None,
                     scm=None,
                     directory=None,
                     output_stream=sys.stdout,
                   ):
    scm, directory = _GetSCMAndDir(scm, directory)
    return CommandLine.DisplayOutput(0, scm.GetChangedFiles(directory, revision), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( filename=CommandLine.FilenameTypeInfo(),
                                  scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def EnumBlameInfo( filename,
                   scm=None,
                   directory=None,
                   output_stream=sys.stdout,
                 ):
    scm, directory = _GetSCMAndDir(scm, directory)

    common_prefix = FileSystem.GetCommonPath(filename, directory)
    if not common_prefix:
        raise CommandLine.UsageException("'{}' must be within the repository root of '{}'.".format(filename, directory))

    return CommandLine.DisplayOutput(0, scm.EnumBlameInfo(directory, filename), output_stream=output_stream)

# ---------------------------------------------------------------------------
# |  Distributed SCM Methods

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Reset( no_prompt=False,
           no_backup=False,
           scm=None,
           directory=None,
           output_stream=sys.stdout,
         ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(*scm.Reset(directory, no_prompt=no_prompt, no_backup=no_backup), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def HasUpdateChanges( scm=None,
                      directory=None,
                      output_stream=sys.stdout,
                    ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(0, scm.HasUpdateChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def HasLocalChanges( scm=None,
                     directory=None,
                     output_stream=sys.stdout,
                   ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(0, scm.HasLocalChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetLocalChanges( scm=None,
                     directory=None,
                     output_stream=sys.stdout,
                   ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(0, scm.GetLocalChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def HasRemoteChanges( scm=None,
                      directory=None,
                      output_stream=sys.stdout,
                    ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(0, scm.HasRemoteChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def GetRemoteChanges( scm=None,
                      directory=None,
                      output_stream=sys.stdout,
                    ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(0, scm.GetRemoteChanges(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Push( scm=None,
          directory=None,
          output_stream=sys.stdout,
        ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(*scm.Push(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Pull( scm=None,
          directory=None,
          output_stream=sys.stdout,
        ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    return CommandLine.DisplayOutput(*scm.Pull(directory), output_stream=output_stream)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( scm=_SCMOptionalTypeInfo,
                                  directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def PullAndUpdate( scm=None,
                   directory=None,
                   output_stream=sys.stdout,
                 ):
    scm, directory = _GetSCMAndDir(scm, directory)
    if not scm.IsDistributed:
        output_stream.write("'{}' is not a distributed source control management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    result = CommandLine.DisplayOutput(*scm.Pull(directory), output_stream=output_stream)
    if result != 0:
        return result

    result = CommandLine.DisplayOutput(*scm.Update(directory, SCMMod.EmptyUpdateMergeArg()), output_stream=output_stream)
    if result != 0:
        return result

    return 0

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def AllChangeStatus( directory=None,
                     output_stream=sys.stdout,
                   ):
    directory = directory or os.getcwd()

    changes = []
    
    # ----------------------------------------------------------------------
    def Query(scm, directory):
        status = scm.GetChangeStatus(directory)
        if status:
            changes.append(QuickObject( scm=scm,
                                        directory=directory,
                                        status=status,
                                      ))
    
        return None
    
    # ----------------------------------------------------------------------
    
    result = _AllImpl( directory,
                       output_stream,

                       Query,

                       # No Action Required
                       None,
                       None,
                       None,

                       require_distributed=False,
                     )

    if not changes:
        return 0

    # Display the output
    cols = [ 80, 17, 10, 17, 15, 13, 14, 14, ]
    template = "{dir:<%d}  {scm:<%d}  {branch:<%d}  {untracked:<%d}  {working:<%d}  {local:<%d}  {remote:<%d}  {update:<%d}" % tuple(cols)
    
    output_stream.write(textwrap.dedent(
        """\

        {}
        {}
        """).format( template.format( dir="Directory",
                                      scm="SCM",
                                      branch="Branch",
                                      untracked="Untracked Changes",
                                      working="Working Changes",
                                      local="Local Changes",
                                      remote="Remote Changes",
                                      update="Update Changes",
                                    ),
                     template.format( dir='-' * cols[0],
                                      scm='-' * cols[1],
                                      branch='-' * cols[2],
                                      untracked='-' * cols[3],
                                      working='-' * cols[4],
                                      local='-' * cols[5],
                                      remote='-' * cols[6],
                                      update='-' * cols[7],
                                    ),
                   ))

    for change in changes:
        output_stream.write("{}\n".format(template.format( dir=change.directory,
                                                           scm=change.scm.Name,
                                                           branch=change.status.branch,
                                                           untracked=str(change.status.untracked) if change.status.untracked != None else "N/A",
                                                           working=str(change.status.working),
                                                           local=str(change.status.local) if hasattr(change.status, "local") else "N/A",
                                                           remote=str(change.status.remote) if hasattr(change.status, "remote") else "N/A",
                                                           update=str(change.status.update) if hasattr(change.status, "update") else "N/A",
                                                         )))

    return 0

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def AllWorkingChangeStatus( directory=None,
                            output_stream=sys.stdout,
                          ):
    directory = directory or os.getcwd()

    changed_repos = []

    # ---------------------------------------------------------------------------
    def Query(scm, directory):
        result = scm.HasWorkingChanges(directory) or scm.HasUntrackedWorkingChanges(directory)
        if result:
            changed_repos.append((scm, directory))

        return result

    # ---------------------------------------------------------------------------
    
    result = _AllImpl( directory,
                       output_stream,
               
                       Query,
               
                       # No Action required
                       None,
                       None,
                       None,
               
                       require_distributed=True,
                     )
    if result != 0 or not changed_repos:
        return result

    output_stream.write(textwrap.dedent(
        """\
        
        There are working changes in {}:
        {}
        
        """).format( inflect_engine.no("repository", len(changed_repos)),
                     '\n'.join([ "    - {}".format(directory) for scm, directory in changed_repos ]),
                   ))

    return 0

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def UpdateAll( directory=None,
               output_stream=sys.stdout,
             ):
    return _AllImpl( directory,
                     output_stream,

                     lambda scm, directory: not scm.IsDistributed or scm.HasUpdateChanges(directory),

                     "{dir} [{scm}] <Update>",
                     "Updating '{dir}'",
                     lambda scm, directory: scm.Update(directory, SCMMod.EmptyUpdateMergeArg()),

                     require_distributed=False,
                   )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def PushAll( directory=None,
             output_stream=sys.stdout,
           ):
    return _AllImpl( directory,
                     output_stream,

                     lambda scm, directory: scm.HasLocalChanges(directory),

                     "{dir} [{scm}] <Push>",
                     "Pushing '{dir}'",
                     lambda scm, directory: scm.Push(directory),

                     require_distributed=True,
                   )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def PullAll( directory=None,
             output_stream=sys.stdout,
           ):
    return _AllImpl( directory,
                     output_stream,

                     lambda scm, directory: scm.HasRemoteChanges(directory),

                     "{dir} [{scm}] <Pull>",
                     "Pulling '{dir}'",
                     lambda scm, directory: scm.Pull(directory),

                     require_distributed=True,
                   )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def PullAndUpdateAll( directory=None,
                      output_stream=sys.stdout,
                    ):
    # ---------------------------------------------------------------------------
    def Action(scm, directory):

        sink = StringIO()

        for action in [ scm.Pull,
                        lambda d: scm.Update(d, SCMMod.EmptyUpdateMergeArg()),
                      ]:
            result, output = action(directory)
            sink.write(output)

            if result != 0:
                break

            sink.write('\n')

        return result, sink.getvalue().rstrip()

    # ---------------------------------------------------------------------------
    
    return _AllImpl( directory,
                     output_stream,

                     lambda scm, directory: scm.HasRemoteChanges(directory),

                     "{dir} [{scm}] <Pull and Update>",
                     "Pulling/Updating '{dir}'",
                     Action,

                     require_distributed=True,
                   )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _GetSCMAndDir(scm_or_none, dir_or_none):
    dir_or_none = dir_or_none or os.getcwd()

    if scm_or_none:
        for scm in SCMMod.GetPotentialSCMs():
            if scm.Name == scm_or_none:
                return scm, dir_or_none

    return SCMMod.GetSCM(dir_or_none), dir_or_none

# ---------------------------------------------------------------------------
def _GetSCMAndDirs(root_dir):
    scm = SCMMod.GetSCM(root_dir, throw_on_error=False)
    if scm:
        yield scm, root_dir
        return

    for item in os.listdir(root_dir):
        fullpath = os.path.join(root_dir, item)
        if os.path.isdir(fullpath):
            if item in [ "Generated", ]:
                continue

            for result in _GetSCMAndDirs(fullpath):
                yield result

# ---------------------------------------------------------------------------
# <Too many local variables> pylint: disable = R0914
def _AllImpl( directory,
              output_stream,
              
              query_func,                   # def Func(scm, directory) -> Bool

              action_name_template,
              action_status_template,
              action_func,                  # def Func(scm, directory) -> (result, output)

              require_distributed,
            ):
    directory = directory or os.getcwd()

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="Composite Results: ",
                                                   ) as si:
        si.stream.write("Searching for repositories in '{}'...".format(directory))
        with si.stream.DoneManager( done_suffix='\n',
                                  ):
            items = list(_GetSCMAndDirs(directory))

        output = []

        # ---------------------------------------------------------------------------
        def QueryProcess(scm, directory, task_index, _output_stream):
            if not require_distributed or scm.IsDistributed:
                output[task_index] = QuickObject( scm=scm,
                                                  directory=directory,
                                                  result=query_func(scm, directory),
                                                )

        # ---------------------------------------------------------------------------
        
        tasks = []

        for scm, directory in items:
            output.append(None)
            tasks.append(TaskPool.Task( "{} [{}] <Query>".format(directory, scm.Name),
                                        "Querying '{}'".format(directory),
                                        lambda task_index, output_stream, scm=scm, directory=directory: QueryProcess(scm, directory, task_index, output_stream),
                                      ))

        if not tasks:
            return 0

        si.stream.write("Processing {}...".format(inflect_engine.no("repository", len(tasks))))
        with si.stream.DoneManager( done_suffix='\n',
                                  ) as this_dm:
            this_dm.result = TaskPool.Execute( tasks, 
                                               1,
                                               output_stream=this_dm.stream, 
                                             )

        action_items = [ data for data in output if data != None and data.result ]
        
        if action_func:
            if not action_items:
                output_stream.write("There are no repositories to process.\n")
            else:
                tasks = []
                
                for action_item in action_items:
                    template_args = { "dir" : action_item.directory,
                                      "scm" : action_item.scm.Name,
                                    }
                
                    tasks.append(TaskPool.Task( action_name_template.format(**template_args),
                                                action_status_template.format(**template_args),
                                                lambda task_index, output_stream, action_item=action_item: action_func(action_item.scm, action_item.directory),
                                              ))
                
                task_pool_result = TaskPool.Execute( tasks, 
                                                     1, 
                                                     output_stream=output_stream,
                                                     verbose=True,
                                                   )

                si.result = si.result or task_pool_result

        return si.result

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
