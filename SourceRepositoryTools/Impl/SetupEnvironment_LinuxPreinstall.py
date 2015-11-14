# ---------------------------------------------------------------------------
# |  
# |  SetupEnvironment_LinuxPreinstall.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/08/2015 05:10:23 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Performs activities that must be completed before invoking standard setup functionality.
"""

import os
import shutil
import sys
import tempfile
import textwrap

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.stdout.write(textwrap.dedent(
    """\
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # |
    # |  Executing Linux Preinstall functionality.
    # |
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    
    """))
    
# Ensure that basic Python libraries are available
python_dir = os.path.normpath(os.path.join(_script_dir, "..", "..", "Tools", "Python"))
assert os.path.isdir(python_dir), python_dir

dirs = [ os.path.join(python_dir, item) for item in os.listdir(python_dir) if os.path.isdir(os.path.join(python_dir, item)) ]
dirs.sort()

# Assume that standard sorting works for these version numbers
python_src_dir = os.path.join(python_dir, dirs[-1], "src")
assert os.path.isdir(python_src_dir), python_src_dir

# Get all the libraries to install
lib_filenames = [ item for item in os.listdir(python_src_dir) if not item.lower().startswith("python") ]

temp_directory = tempfile.mkdtemp()
assert os.path.isdir(temp_directory), temp_directory

for lib_filename in lib_filenames:
    sys.stdout.write(textwrap.dedent(
        """\
        # ---------------------------------------------------------------------------
        # |
        # |  Installing {}
        # |
        # ---------------------------------------------------------------------------
        
        """).format(lib_filename))

    this_temp_dir = os.path.join(temp_directory, lib_filename)
    this_lib_fullpath = os.path.join(python_src_dir, lib_filename)
    
    os.system(textwrap.dedent(
        """\
        mkdir "{this_temp_dir}"
        tar -zxvf "{this_lib_fullpath}" -C "{this_temp_dir}" > /dev/null
        """).format( this_temp_dir=this_temp_dir,
                     this_lib_fullpath=this_lib_fullpath,
                   ))
    
    setup_filename = None
    
    for root, dirs, filenames in os.walk(this_temp_dir):
        for filename in filenames:
            if filename == "setup.py":
                setup_filename = os.path.join(root, filename)
                break
                
        if setup_filename:
            break
            
    assert setup_filename, this_lib_fullpath
    
    os.system(textwrap.dedent(
        """\
        cd "{dir}"
        python setup.py install
        cd "{original_dir}"
        """).format( dir=os.path.dirname(setup_filename),
                     original_dir=os.getcwd(),
                   ))

    sys.stdout.write("\n\n")
    
shutil.rmtree(temp_directory)
sys.stdout.write("\n\n")