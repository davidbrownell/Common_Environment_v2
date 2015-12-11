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
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

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
            ):
    process_dir_name = _ProcessArgs(include_dir_names, exclude_dir_names)
    process_dir_path = _ProcessArgs(include_dir_paths, exclude_dir_paths)

    process_traverse_dir_name = _ProcessArgs(traverse_include_dir_names, traverse_exclude_dir_names)
    process_traverse_dir_path = _ProcessArgs(traverse_include_dir_paths, traverse_exclude_dir_paths)

    for root, dirs, filenames in os.walk(root):
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

            if not process_traverse_dir_path(fullpath) or not process_traverse_dir_name(dirs[index]):
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

               recurse=True,
             ):
    process_file_name = _ProcessArgs(include_file_names, exclude_file_names)
    process_file_base_name = _ProcessArgs(include_file_base_names, exclude_file_base_names)
    process_file_extension = _ProcessArgs(include_file_extensions, exclude_file_extensions)
    
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
                                   ):
        for filename in filenames:
            if not process_file_name(filename):
                continue

            base_name, ext = os.path.splitext(filename)
            if ( not process_file_extension(ext) or 
                 not process_file_base_name(base_name)
               ):
                continue

            yield os.path.join(root, filename)

# ---------------------------------------------------------------------------
_GetCommonPath_Compare = None

def GetCommonPath(*items):
    if not items:
        return ''

    # Determine if we are on a case insensitive file systme. If so, comparisons can
    # be more forgiving.
    if _GetCommonPath_Compare == None:
        assert os.path.exists(items[0]), items[0]
        is_case_insensitive = os.path.isfile(items[0].upper())

        if is_case_insensitive:
            # ---------------------------------------------------------------------------
            def Compare(a, b):
                return a.lower() == b.lower()

            # ---------------------------------------------------------------------------
        else:
            # ---------------------------------------------------------------------------
            def Compare(a, b):
                return a == b
            
            # ---------------------------------------------------------------------------

    # Break the items into parts, as comparing by string leads to strange corner cases
    # with similarly named paths.
    items = [ os.path.realpath(item).split(os.path.sep) for item in items]

    path_index = 0
    while True:
        should_continue = True
        
        for item_index, item in enumerate(items):
            if path_index >= len(item):
                should_continue = False
                break

            if item_index != 0 and not Compare(items[item_index][path_index], items[item_index - 1][path_index]):
                should_continue = False
                break

        if not should_continue:
            break

        path_index += 1

    if path_index == 0:
        return ''

    return "{}{}".format(os.path.sep.join(items[0][:path_index]), os.path.sep)

# ---------------------------------------------------------------------------
def GetRelativePath(source, dest):
    assert source
    assert dest

    if os.path.isfile(source):
        source = os.path.dirname(source)

    # ---------------------------------------------------------------------------
    def StripTrailingSep(item):
        return item if not item.endswith(os.path.sep) else item[:-len(os.path.sep)]

    # ---------------------------------------------------------------------------
    
    source = StripTrailingSep(source)
    dest = StripTrailingSep(dest)

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

# ---------------------------------------------------------------------------
def Normalize(path):
    drive, suffix = os.path.splitdrive(os.path.normpath(path))
    return "{}{}".format(drive.upper(), suffix)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _ProcessArgs(include_items, exclude_items):

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
            elif callable(item) and item(value):
                return True
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
