# ---------------------------------------------------------------------------
# |  
# |  FileSystem.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/05/2015 08:47:49 PM
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
import platform
import shutil
import stat
import sys
import time

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

CODE_EXCLUDE_DIR_NAMES                      = [ "Generated",
                                                "__pycache__",
                                                ".hg",                      # Mercurial
                                                ".git",                     # Git
                                                ".svn",                     # Subversion
                                                "$tf",                      # Team Foundation
                                              ]

CODE_EXCLUDE_FILE_EXTENSIONS                = [ # Python
                                                ".pyc",
                                                ".pyo",
                                              ]

# ----------------------------------------------------------------------
if platform.uname()[0] == "Windows":
    import win32api

    _is_case_sensitive_file_system = False
else:
    _is_case_sensitive_file_system = True

# ---------------------------------------------------------------------------
def WalkDirs( root,
              
              include_dir_names=None,                   # ex. "ASingleDir"
              exclude_dir_names=None,                   # ex. "ASingleDir"

              include_dir_paths=None,                   # ex. "C:\Foo\Bar"
              exclude_dir_paths=None,                   # ex. "C:\Foo\Bar"

              traverse_include_dir_names=None,          # ex. "ASingleDir"
              traverse_exclude_dir_names=None,          # ex. "ASingleDir"

              traverse_include_dir_paths=None,          # ex. "C:\Foo\Bar"
              traverse_exclude_dir_paths=None,          # ex. "C:\Foo\Bar"

              recurse=True,
              include_generated=False,
            ):
    process_dir_name = _ProcessWalkArgs(include_dir_names, exclude_dir_names)
    process_dir_path = _ProcessWalkArgs(include_dir_paths, exclude_dir_paths)

    process_traverse_dir_name = _ProcessWalkArgs(traverse_include_dir_names, traverse_exclude_dir_names)
    process_traverse_dir_path = _ProcessWalkArgs(traverse_include_dir_paths, traverse_exclude_dir_paths)

    if include_generated:
        # ----------------------------------------------------------------------
        def IsValid(fullpath, dir):
            return ( process_traverse_dir_path(fullpath) and
                     process_traverse_dir_name(dir)
                   )

        # ----------------------------------------------------------------------

    else:
        # ----------------------------------------------------------------------
        def IsValid(fullpath, dir):
            return ( dir not in CODE_EXCLUDE_DIR_NAMES and
                     process_traverse_dir_path(fullpath) and
                     process_traverse_dir_name(dir)
                   )

        # ----------------------------------------------------------------------

    from CommonEnvironment.CallOnExit import CallOnExit

    root = Normalize(root)

    for root, dirs, filenames in os.walk(root):
        try:
            root = str(root)
        except UnicodeEncodeError:
            continue
        
        root = os.path.realpath(root)
        
        # Ensure that the drive letter is uppercase
        drive, path = os.path.splitdrive(root)
        drive = drive.upper()

        root = "{}{}".format(drive, path)

        if process_dir_path(root) and process_dir_name(os.path.split(root)[1]):
            yield root, filenames

        index = 0
        while index < len(dirs):
            fullpath = os.path.join(root, dirs[index])

            if not IsValid(fullpath, dirs[index]):
                dirs.pop(index)
            else:
                index += 1

        if not recurse:
            dirs[:] = []

# ---------------------------------------------------------------------------
def WalkFiles( root,
               
               include_dir_names=None,                  # ex. "ASingleDir"
               exclude_dir_names=None,                  # ex. "ASingleDir"

               include_dir_paths=None,                  # ex. "c:\foo\bar"
               exclude_dir_paths=None,                  # ex. "c:\foo\bar"

               traverse_include_dir_names=None,         # ex. "ASingleDir"
               traverse_exclude_dir_names=None,         # ex. "ASingleDir"

               traverse_include_dir_paths=None,         # ex. "C:\foo\bar"
               traverse_exclude_dir_paths=None,         # ex. "C:\foo\bar"

               include_file_base_names=None,            # ex. "File" where filename is "File.ext"
               exclude_file_base_names=None,            # ex. "File" where filename is "File.ext"            

               include_file_extensions=None,            # ex. ".py"
               exclude_file_extensions=None,            # ex. ".py"

               include_file_names=None,                 # ex. "File.ext"
               exclude_file_names=None,                 # ex. "File.ext"

               include_full_paths=None,                 # ex. "C:\foo\bar\file.ext"
               exclude_full_paths=None,                 # ex. "C:\foo\bar\file.ext"

               recurse=True,
               include_generated=False,
             ):
    process_file_name = _ProcessWalkArgs(include_file_names, exclude_file_names)
    process_file_base_name = _ProcessWalkArgs(include_file_base_names, exclude_file_base_names)
    process_file_extension = _ProcessWalkArgs(include_file_extensions, exclude_file_extensions)
    process_full_path = _ProcessWalkArgs(include_full_paths, exclude_full_paths)

    for root, filenames in WalkDirs( root,
                                     include_dir_names=include_dir_names,
                                     exclude_dir_names=exclude_dir_names,
                                     include_dir_paths=include_dir_paths,
                                     exclude_dir_paths=exclude_dir_paths,
                                     traverse_include_dir_names=traverse_include_dir_names,
                                     traverse_exclude_dir_names=traverse_exclude_dir_names,
                                     traverse_include_dir_paths=traverse_include_dir_paths,
                                     traverse_exclude_dir_paths=traverse_exclude_dir_paths,
                                     recurse=recurse,
                                     include_generated=include_generated,
                                   ):
        for filename in filenames:
            if not process_file_name(filename):
                continue

            base_name, ext = os.path.splitext(filename)
            if ( not process_file_extension(ext) or 
                 not process_file_base_name(base_name)
               ):
                continue

            fullpath = os.path.join(root, filename)

            if not process_full_path(fullpath):
                continue

            yield fullpath

# ----------------------------------------------------------------------
def EnumSubdirs( root, 
                 names=False,
                 fullpaths=True, 
               ):
    assert os.path.isdir(root), root

    if names and fullpaths:
        Decorator = lambda name, fullpath: (name, fullpath)
    elif names:
        Decorator = lambda name, fullpath: name
    elif fullpaths:
        Decorator = lambda name, fullpath: fullpath
    else:
        assert False

    for name in os.listdir(root):
        fullpath = os.path.join(root, name)
        if not os.path.isdir(fullpath):
            continue

        yield Decorator(name, fullpath)

# ---------------------------------------------------------------------------
def GetCommonPath(*items):
    if not items:
        return ''

    if not _is_case_sensitive_file_system:
        # ----------------------------------------------------------------------
        def Equal(a, b):
            return a.lower() == b.lower()

        # ----------------------------------------------------------------------
        
    else:
        # ----------------------------------------------------------------------
        def Equal(a, b):
            return a == b

        # ----------------------------------------------------------------------
        
    if len(items) == 1:
        result = items[0]

        if os.path.isfile(result):
            result = os.path.dirname(result)

        return AddTrailingSep(result)

    # Break the items into parts, as comparing by string leads to strange corner cases
    # with similarly named paths.
    items = [ os.path.realpath(item).split(os.path.sep) for item in items ]

    path_index = 0
    while True:
        should_continue = True
        
        for item_index, item in enumerate(items):
            if path_index >= len(item):
                should_continue = False
                break

            if item_index != 0 and not Equal(items[item_index][path_index], items[item_index - 1][path_index]):
                should_continue = False
                break

        if not should_continue:
            break

        path_index += 1

    if path_index == 0:
        return ''

    return AddTrailingSep(os.path.sep.join(items[0][:path_index]))

# ---------------------------------------------------------------------------
def GetRelativePath(source, dest):
    assert source
    assert dest

    if os.path.isfile(source):
        source = os.path.dirname(source)

    source = RemoveTrailingSep(source)
    dest = RemoveTrailingSep(dest)

    common_prefix = GetCommonPath(source, dest)

    if not common_prefix:
        return dest

    dest = dest[len(common_prefix):]
    if dest.startswith(os.path.sep):
        dest = dest[len(os.path.sep):]

    source = source[len(common_prefix):]

    seps = 0
    for part in os.path.splitdrive(source)[1].split(os.path.sep):
        if part: seps += 1

    if not seps:
        return os.path.join(".", dest)

    return "{}{}".format((("..{}".format(os.path.sep)) * seps), dest)

# ---------------------------------------------------------------------------
def RemoveTrailingSep(path):
    if path == None:
        return None

    if path.endswith(os.path.sep):
        path = path[:-len(os.path.sep)]

    return path

# ----------------------------------------------------------------------
def AddTrailingSep(path):
    if not path.endswith(os.path.sep):
        path += os.path.sep

    return path

# ----------------------------------------------------------------------
def RemoveInitialSep(path):
    if path.startswith(os.path.sep):
        path = path[len(os.path.sep):]

    return path

# ---------------------------------------------------------------------------
def Normalize(path):
    path = os.path.normpath(path)

    if not _is_case_sensitive_file_system:
        if os.path.exists(path):
            path = win32api.GetLongPathName(win32api.GetShortPathName(path))    # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

        drive, suffix = os.path.splitdrive(path)
        path = "{}{}".format(drive.upper(), suffix)

    return path

# ----------------------------------------------------------------------
def GetSizeDisplay(num_bytes, suffix='B'):
    for unit in [ '', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', ]:
        if num_bytes < 1024.0:
            return "%3.1f %s%s" % (num_bytes, unit, suffix)
        num_bytes /= 1024.0

    return "%.1f %s%s" % (num_bytes, 'Yi', suffix)

# ----------------------------------------------------------------------
def CopyTree(source, dest):
    for fullpath in WalkFiles(source):
        this_dest = dest + fullpath[len(source):]
        this_dest_dir = os.path.dirname(this_dest)

        if not os.path.isdir(this_dest_dir):
            os.makedirs(this_dest_dir)

        shutil.copy(fullpath, this_dest)

# ----------------------------------------------------------------------
def RemoveTree( path,
                optional_retry_iterations=5,
              ):
    if not os.path.isdir(path):
        return False
        
    from CommonEnvironment import Shell

    environment = Shell.GetEnvironment()

    _RemoveImpl(environment.RemoveDir, path, optional_retry_iterations)
    return True

# ----------------------------------------------------------------------
def RemoveFile( path,
                optional_retry_iterations=5,            # Can be None
              ):
    if not os.path.isfile(path):
        return False

    _RemoveImpl(os.remove, path, optional_retry_iterations)
    return True

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _ProcessWalkArgs(include_items, exclude_items):

    # ---------------------------------------------------------------------------
    def Preprocess(items):
        if items == None:
            return []

        if isinstance(items, list):
            return items

        return [ items, ]

    # ---------------------------------------------------------------------------
    def In(value, items):
        for item in items:
            if isinstance(item, str) and item == value:
                return True
            
            elif callable(item):
                try:
                    if item(value):
                        return True
                except:
                    pass
            
            elif hasattr(item, "match") and item.match(value):
                return True

        return False

    # ---------------------------------------------------------------------------
    
    include_items = Preprocess(include_items)
    exclude_items = Preprocess(exclude_items)

    # ---------------------------------------------------------------------------
    def Impl(value):
        if exclude_items and In(value, exclude_items):
            return False

        if include_items and not In(value, include_items):
            return False

        return True

    # ---------------------------------------------------------------------------
    
    return Impl

# ---------------------------------------------------------------------------
def _RemoveImpl( func,                          # def Func(renamed_path)
                 path, 
                 optional_retry_iterations,
               ):
    assert os.path.exists(path), path

    # Rename the dir or item to a temporary one and then remove
    # the renamed item. This works around timing issues associated
    # with quickly creating an item after it has just been deleted.
    iteration = 0

    while True:
        potential_renamed_path = "{}{}".format(path, iteration)
        if not os.path.exists(potential_renamed_path):
            renamed_path = potential_renamed_path
            break

        iteration += 1

    # Invoke
    iteration = 0
    while True:
        try:
            os.rename(path, renamed_path)
            break
        except:
            if optional_retry_iterations != None:
                # Handle temporary permission denied errors by retrying after a 
                # period of time.
                time.sleep(1) # seconds

                iteration += 1
                if iteration < optional_retry_iterations:
                    continue

            raise

    func(renamed_path)
