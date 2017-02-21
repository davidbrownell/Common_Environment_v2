# ----------------------------------------------------------------------
# |  
# |  Backup.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-01-07 09:39:24
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Processes files for offsite or mirrored backup.
"""

import hashlib
import itertools
import os
import re
import shutil
import sys
import textwrap

from collections import OrderedDict
import cPickle as pickle

import inflect

from CommonEnvironment import Any
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect_engine                              = inflect.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint( backup_name=CommandLine.EntryPoint.ArgumentInfo("Name used to uniquely identify the backup"),
                         output_dir=CommandLine.EntryPoint.ArgumentInfo("Output directory that will contain the compressed file(s)"),
                         input=CommandLine.EntryPoint.ArgumentInfo("One or more filenames or directories used to parse for input"),
                         force=CommandLine.EntryPoint.ArgumentInfo("Ignore previously saved information when calculating work to execute"),
                         include=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify filenames to include"),
                         exclude=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify filenames to exclude"),
                         traverse_include=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify directory names to include while parsing"),
                         traverse_exclude=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify directory names to exclude while parsing"),
                         display=CommandLine.EntryPoint.ArgumentInfo("Display the operations that would be taken but do not perform them"),
                         password=CommandLine.EntryPoint.ArgumentInfo("Compress with a password"),
                       )
@CommandLine.FunctionConstraints( backup_name=CommandLine.StringTypeInfo(),
                                  output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                  include=CommandLine.StringTypeInfo(arity='*'),
                                  exclude=CommandLine.StringTypeInfo(arity='*'),
                                  traverse_include=CommandLine.StringTypeInfo(arity='*'),
                                  traverse_exclude=CommandLine.StringTypeInfo(arity='*'),
                                  password=CommandLine.StringTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Offsite( backup_name,
             output_dir,
             input,
             force=False,
             include=None,
             exclude=None,
             traverse_include=None,
             traverse_exclude=None,
             display=False,
             password=None,
             output_stream=sys.stdout,
             verbose=False,
           ):
    """\
    Calculates data to modify based on statistics produced during previous invocations.
    """

    inputs = input; del input
    includes = include; del include
    excludes = exclude; del exclude
    traverse_includes = traverse_include; del traverse_include
    traverse_excludes = traverse_exclude; del traverse_exclude
        
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nResults: ",
                                                   ) as dm:
        environment = Shell.GetEnvironment()

        pickle_filename = environment.CreateDataFilename("{}.backup".format(backup_name))

        source_file_info = _GetFileInfo( "source",
                                         inputs,
                                         includes,
                                         excludes,
                                         traverse_includes,
                                         traverse_excludes,
                                         dm.stream,
                                       )
        dm.stream.write("\n")

        if not force and os.path.isfile(pickle_filename):
            try:
                dest_file_info = pickle.load(open(pickle_filename))
            except:
                dm.stream.write("WARNING: The previously saved data appears to be corrupt and will not be used.\n")
                dest_file_info = {}
        else:
            dest_file_info = {}

        # Calculate work to complete
        to_copy, to_remove = _CreateWork( source_file_info,
                                          dest_file_info,
                                          None,
                                          dm.stream,
                                          verbose,
                                        )

        if display:
            _Display(to_copy, to_remove, dm.stream)

        else:
            if os.path.isdir(output_dir):
                dm.stream.write("Removing existing content in '{}'...".format(output_dir))
                with dm.stream.DoneManager():
                    FileSystem.RemoveTree(output_dir)

            # Organize the files by drive
            to_copy_by_drive = {}
            to_remove_by_drive = {}

            for filename in to_copy.iterkeys():
                to_copy_by_drive.setdefault(os.path.splitdrive(filename)[0], []).append(filename)

            for filename in to_remove:
                to_remove_by_drive.setdefault(os.path.splitdrive(filename)[0], []).append(filename)

            previous_dir = os.getcwd()
            with CallOnExit(lambda: os.chdir(previous_dir)):
                command_line_template = '7z a -t7z "{{output_filename}}" -mx9 -v{chunk_size}b -scsWIN -ssw -y{password} -slp "@{{arg_filename}}"' \
                                            .format( chunk_size=250 * 1024 * 1024, # 250Mb,
                                                     password='' if not password else ' "-p{}"'.format(password),
                                                   )

                # ----------------------------------------------------------------------
                def ProcessToRemove(drive):
                    if drive not in to_remove_by_drive:
                        return

                    # Create a filename tht contains all of the filename to remove
                    remove_filename = "__RemoveFiles__.txt"

                    if drive:
                        remove_filename = os.path.join(drive, remove_filename)
                    else:
                        remove_filename = "{}{}".format(os.path.sep, remove_filename)

                    with open(remove_filename, 'w') as f:
                        f.write('\n'.join(to_remove_by_drive[drive]))

                    del to_remove_by_drive[drive]
                    
                    return remove_filename

                # ----------------------------------------------------------------------
                def Compress(drive, filenames):
                    drive_suffix = ''

                    if drive:
                        if len(to_copy_by_drive) > 1 or len(to_remove_by_drive) > 1:
                            drive_suffix = ".{}".format(drive.replace(':', '_'))
                        
                        this_drive = drive
                        if not this_drive.endswith(os.path.sep):
                            this_drive += os.path.sep

                        os.chdir(this_drive)
                        
                    else:
                        os.chdir(os.path.sep)

                    remove_filename = ProcessToRemove(drive)

                    if remove_filename:
                        filenames.append(remove_filename)
                        Cleanup = lambda: os.remove(remove_filename)
                    else:
                        Cleanup = lambda: None

                    with CallOnExit(Cleanup):
                        # Create the arg filename
                        arg_filename = environment.CreateTempFilename()

                        with open(arg_filename, 'w') as f:
                            for filename in filenames:
                                drive, filename = os.path.splitdrive(filename)
                                if filename.startswith(os.path.sep):
                                    filename = filename[len(os.path.sep):]

                                f.write("{}\n".format(filename))

                        with CallOnExit(lambda: os.remove(arg_filename)):
                            dm.stream.write("Compressing{}...".format('' if not drive else " {}".format(drive)))
                            with dm.stream.DoneManager( done_suffix='\n',
                                                      ) as this_dm:
                                command_line = command_line_template.format( output_filename=os.path.join(output_dir, "Backup{}.7z".format(drive_suffix)),
                                                                             arg_filename=arg_filename,
                                                                           )
                                this_dm.result = Process.Execute( command_line,
                                                                  this_dm.stream,
                                                                )
                                
                # ----------------------------------------------------------------------
                
                for drive, filenames in to_copy_by_drive.iteritems():
                    Compress(drive, filenames)

                for drive in to_remove_by_drive.keys():
                    Compress(drive, [])

        if dm.result == 0 and (to_copy or to_remove):
            # Persist the data
            with open(pickle_filename, 'w') as f:
                pickle.dump(source_file_info, f)

            return 0

        return dm.result or 1

# ----------------------------------------------------------------------
@CommandLine.EntryPoint( destination=CommandLine.EntryPoint.ArgumentInfo("Destination directory"),
                         input=CommandLine.EntryPoint.ArgumentInfo("One or more filenames or directories used to parse for input"),
                         force=CommandLine.EntryPoint.ArgumentInfo("Ignore information in the destination when calculating work to execute"),
                         include=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify filenames to include"),
                         exclude=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify filenames to exclude"),
                         traverse_include=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify directory names to include while parsing"),
                         traverse_exclude=CommandLine.EntryPoint.ArgumentInfo("One or more regular expressions used to specify directory names to exclude while parsing"),
                         display=CommandLine.EntryPoint.ArgumentInfo("Display the operations that would be taken but do not perform them"),
                       )
@CommandLine.FunctionConstraints( destination=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                  include=CommandLine.StringTypeInfo(arity='*'),
                                  exclude=CommandLine.StringTypeInfo(arity='*'),
                                  traverse_include=CommandLine.StringTypeInfo(arity='*'),
                                  traverse_exclude=CommandLine.StringTypeInfo(arity='*'),
                                  output_stream=None,
                                )
def Mirror( destination,
            input,
            force=False,
            include=None,
            exclude=None,
            traverse_include=None,
            traverse_exclude=None,
            display=False,
            output_stream=sys.stdout,
            verbose=False,
          ):
    """\
    Mirrors files to a different location. Both the input source and destination are 
    scanned when calculating the operations necessary to ensure that the destination
    matches the input source(s).
    """

    destination = FileSystem.Normalize(destination)
    inputs = [ FileSystem.Normalize(i) for i in input ]; del input
    includes = include; del include
    excludes = exclude; del exclude
    traverse_includes = traverse_include; del traverse_include
    traverse_excludes = traverse_exclude; del traverse_exclude
        
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nResults: ",
                                                   ) as dm:
        source_file_info = _GetFileInfo( "source",
                                         inputs,
                                         includes,
                                         excludes,
                                         traverse_includes,
                                         traverse_excludes,
                                         dm.stream,
                                       )
        dm.stream.write("\n")

        if not force and os.path.isdir(destination):
            dest_file_info = _GetFileInfo( "destination",
                                           [ destination, ],
                                           None,
                                           None,
                                           None,
                                           None,
                                           dm.stream,
                                         )

            # _CreateWork expects a dictionary organized by original source drive;
            # Perform that conversion.
            new_dest_file_info = OrderedDict()
            len_normalized_destination = len(FileSystem.AddTrailingSep(destination))

            assert len(dest_file_info) <= 1, dest_file_info.keys()
            if dest_file_info:
                for k, v in dest_file_info.values()[0].iteritems():
                    assert len(k) > len_normalized_destination, k
                
                    potential_drive = k[len_normalized_destination:].split(os.path.sep)[0]
                    if potential_drive.endswith('_') and len(potential_drive) <= 3:
                        drive = potential_drive.replace('_', ':')
                    else:
                        assert len(source_file_info) == 1, source_file_info.keys()
                        assert source_file_info.values()[0]

                        drive = os.path.splitdrive(source_file_info.values()[0].keys()[0])[0]

                    new_dest_file_info.setdefault(drive, {})[k] = v
                
                dest_file_info = new_dest_file_info

            dm.stream.write("\n")
        else:
            dest_file_info = {}

        # Calculate the work to complete
        to_copy, to_remove = _CreateWork( source_file_info,
                                          dest_file_info,
                                          destination,
                                          dm.stream,
                                          verbose,
                                        )

        if display:
            _Display(to_copy, to_remove, dm.stream)
        
        else:
            if not os.path.isdir(destination):
                os.makedirs(destination)
        
            if to_copy:
                desc = "Copying {}...".format(inflect_engine.no("file", len(to_copy)))
            
                dm.stream.write(desc)
                with dm.stream.DoneManager( done_prefix="\033[1A{}DONE! ".format(desc),
                                          ) as this_dm:
                    # ----------------------------------------------------------------------
                    def Execute(task_index, task_output):
                        try:
                            k = to_copy.keys()[task_index]
                            v = to_copy[k]
            
                            dest_dir = os.path.dirname(v)
                            if not os.path.isdir(dest_dir):
                                os.makedirs(dest_dir)
            
                            shutil.copyfile(k, v)
                        except Exception, ex:
                            task_output.write(str(ex))
                            return -1
            
                    # ----------------------------------------------------------------------
                    
                    this_dm.result = TaskPool.Execute( [ TaskPool.Task( "Copy '{}' to '{}'".format(k, v),
                                                                        "Copying '{}' to '{}'".format(k, v),
                                                                        Execute,
                                                                      )
                                                         for k, v in to_copy.iteritems()
                                                       ],
                                                       num_concurrent_tasks=1,
                                                       output_stream=this_dm.stream,
                                                       progress_bar=True,
                                                     )
            
            if to_remove:
                desc = "Removing {}...".format(inflect_engine.no("file", len(to_remove)))
            
                dm.stream.write(desc)
                with dm.stream.DoneManager( done_prefix="\033[1A{}DONE! ".format(desc),
                                          ) as this_dm:
                    # ----------------------------------------------------------------------
                    def Execute(task_index, task_output):
                        try:
                            value = to_remove[task_index]
            
                            os.remove(value)
                        except Exception, ex:
                            task_output.write(str(ex))
                            return -1
            
                    # ----------------------------------------------------------------------
                    
                    this_dm.result = TaskPool.Execute( [ TaskPool.Task( "Remove '{}'".format(value),
                                                                        "Removing '{}'".format(value),
                                                                        Execute,
                                                                      )
                                                         for value in to_remove
                                                       ],
                                                       num_concurrent_tasks=1,
                                                       output_stream=this_dm.stream,
                                                       progress_bar=True,
                                                     )

        return dm.result or (1 if not (to_copy or to_remove) else 0)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetFileInfo( desc,
                  inputs,
                  includes,
                  excludes,
                  traverse_includes,
                  traverse_excludes,
                  output_stream,
                ):
    output_stream.write("Processing {}...".format(desc))
    with StreamDecorator(output_stream).DoneManager() as dm:
        input_files = []

        dm.stream.write("Processing files...")
        with dm.stream.DoneManager( done_suffix_functor=lambda: "{} found".format(inflect_engine.no("file", len(input_files))),
                                  ) as file_dm:
            input_dirs = []

            for i in inputs:
                if os.path.isfile(i):
                    input_files.append(i)
                elif os.path.isdir(i):
                    input_dirs.append(i)
                else:
                    assert False, i

            if input_dirs:
                file_dm.stream.write("Processing {}...".format(inflect_engine.no("directory", len(input_dirs))))
                with file_dm.stream.DoneManager():
                    for input_dir in input_dirs:
                        input_files += FileSystem.WalkFiles( input_dir,
                                                             traverse_include_dir_paths=traverse_includes,
                                                             traverse_exclude_dir_paths=traverse_excludes,
                                                           )

        if includes or excludes:
            # ----------------------------------------------------------------------
            def ToRegexes(items):
                results = []

                for item in items:
                    try:
                        results.append(re.compile(item))
                    except:
                        raise CommandLine.UsageException("'{}' is not a valid regular expression".format(item))

                return results

            # ----------------------------------------------------------------------
        
            dm.stream.write("Filtering files...")
            with dm.stream.DoneManager( lambda: "{} to process".format(inflect_engine.no("file", len(input_files))),
                                      ):
                if includes:
                    include_regexes = ToRegexes(includes)
                    IncludeChecker = lambda input_file: Any(include_regexes, lambda regex: regex.match(input_files))
                else:
                    IncludeChecker = lambda input_file: True

                if excludes:
                    exclude_regexes = ToRegexes(excludes)
                    ExcludeChecker = lambda input_file: Any(exclude_regexes, lambda regex: regex.match(input_file))
                else:
                    ExcludeChecker = lambda input_file: False

                valid_files = []

                for input_file in input_files:
                    if not ExcludeChecker(input_file) and IncludeChecker(input_file):
                        valid_files.append(input_file)

                input_files[:] = valid_files

        # Hash each file
        file_info = OrderedDict()

        # ----------------------------------------------------------------------
        def CalculateHash(filename):
            md5 = hashlib.md5()

            with open(filename) as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break

                    md5.update(data)

                return md5.hexdigest()

        # ----------------------------------------------------------------------
        
        if input_files:
            dm.stream.write("Calculating hashes...")
            with dm.stream.DoneManager( done_prefix="\033[1A  Calculating hashes...DONE! ",
                                      ) as this_dm:
                for k, v in itertools.izip( input_files,
                                            TaskPool.Transform( input_files,
                                                                CalculateHash,
                                                                this_dm.stream,
                                                              ),
                                          ):
                    file_info.setdefault(os.path.splitdrive(k)[0], OrderedDict())[k] = v

        return file_info

# ----------------------------------------------------------------------
def _CreateWork( source_file_info,
                 dest_file_info,
                 destination,               # Can be None
                 output_stream,
                 verbose,
               ):
    to_copy = OrderedDict()
    to_remove = []

    output_stream.write("Processing file information...")
    with StreamDecorator(output_stream).DoneManager( done_suffix_functor=[ lambda: "{} to copy".format(inflect_engine.no("file", len(to_copy))),
                                                                           lambda: "{} to remove".format(inflect_engine.no("file", len(to_remove))),
                                                                         ],
                                                     done_suffix='\n',
                                                   ) as dm:
        verbose_stream = StreamDecorator(dm.stream if verbose else None, "INFO: ")

        # ----------------------------------------------------------------------
        def CreatePathConversionFunctions(drive, items):
            common_path = FileSystem.GetCommonPath(*items.keys())
            if not common_path and len(items) == 1:
                common_path = FileSystem.AddTrailingSep(os.path.dirname(items.keys()[0]))

            assert common_path
                
            # ----------------------------------------------------------------------
            def CreateToDestFullPath():
                if destination == None:
                    return lambda filename: filename

                common_path_len = len(common_path)

                if len(source_file_info) == 1:
                    return lambda filename: os.path.join(destination, filename[common_path_len:])

                dest_drive_dir = drive.replace(':', '_')
                
                return lambda filename: os.path.join(destination, dest_drive_dir, filename[common_path_len:])

            # ----------------------------------------------------------------------
            def CreateToSourceFullPath():
                if destination == None:
                    return lambda filename: filename

                destination_path_len = len(FileSystem.AddTrailingSep(destination))

                if len(source_file_info) == 1:
                    drive_delta = 0
                else:
                    drive_delta = len(drive) + len(os.path.sep)

                return lambda filename: os.path.join(common_path, filename[destination_path_len + drive_delta:])

            # ----------------------------------------------------------------------

            return CreateToDestFullPath(), CreateToSourceFullPath()

        # ----------------------------------------------------------------------
        
        for drive, this_source_file_info in source_file_info.iteritems():
            ToDestFullPath, ToSourceFullPath = CreatePathConversionFunctions(drive, this_source_file_info)
            
            this_dest_file_info = dest_file_info.get(drive, {})

            # Files to copy
            for k, v in this_source_file_info.iteritems():
                dest_filename = ToDestFullPath(k)
                
                copy = False

                if dest_filename not in this_dest_file_info:
                    verbose_stream.write("[Add] '{}' does not exist.\n".format(k))
                    copy = True
                elif this_dest_file_info[dest_filename] != v:
                    verbose_stream.write("[Add] '{}' has changed.\n".format(k))
                    copy = True
                    
                if copy:
                    to_copy[k] = dest_filename

            # Files to remove
            for k, v in this_dest_file_info.iteritems():
                source_filename = ToSourceFullPath(k)
                
                if source_filename not in this_source_file_info:
                    verbose_stream.write("[Remove] '{}' does not exist.\n".format(source_filename))
                    to_remove.append(k)

        for drive, this_dest_file_info in dest_file_info.iteritems():
            if drive not in source_file_info:
                for k in this_dest_file_info.iterkeys():
                    source_filename = ToSourceFullPath(k)

                    verbose_stream.write("[Remove] '{}' does not exist.\n".format(k))
                    to_remove.append(k)

        return to_copy, to_remove
              
# ----------------------------------------------------------------------
def _Display(to_copy, to_remove, output_stream):
    copy_header = "Source files to copy ({})".format(len(to_copy))
    remove_header = "Destination files to remove ({})".format(len(to_remove))

    output_stream.write(textwrap.dedent(
        """\
        {}
        {}
        {}

        {}
        {}
        {}

        """).format( copy_header,
                     '-' * len(copy_header),
                     '\n'.join([ "{0:<100} -> {1}".format(k, v) for k, v in to_copy.iteritems() ]),
                     remove_header,
                     '-' * len(remove_header),
                     '\n'.join(to_remove),
                   ))
                                
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
