# ----------------------------------------------------------------------
# |  
# |  AcquireBinaries.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-04-29 18:28:02
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import shutil
import sys
import textwrap
import zipfile

import six
import tqdm

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

UNIQUE_ID_FILENAME = "__AcquireBinariesUniqueId__"

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( repo_name=CommandLine.StringTypeInfo(),
                                  url=CommandLine.StringTypeInfo(),
                                  base_dir=CommandLine.DirectoryTypeInfo(),
                                  unique_id=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def EntryPoint( repo_name,
                url,
                base_dir,
                unique_id=None,
                output_stream=sys.stdout,
              ):
    binary_name = os.path.basename(url)
    binary_name, binary_ext = os.path.splitext(binary_name)

    # Calculate the output dir based on the base_dir and the binary of the binary
    assert binary_name.startswith(repo_name), (binary_name, repo_name)
    assert binary_name[len(repo_name)] == '-'

    output_dir = os.path.join(base_dir, *tuple([ six.moves.urllib.parse.unquote(item) for item in binary_name[len(repo_name) + 1:].split('-') ]))
    
    # Don't do anything if the repo already exists
    if os.path.isdir(output_dir):
        if not unique_id or (unique_id and os.path.isfile(os.path.join(output_dir, UNIQUE_ID_FILENAME)) and open(os.path.join(output_dir, UNIQUE_ID_FILENAME)).read().strip() == unique_id):
            output_stream.write(textwrap.dedent(
                """\
                The content at '{}' already exists and will not be overwritten.
                Please delete the directory if this content is no longer valid or needs to be downloaded again.

                """).format(output_dir))

            return

        shutil.rmtree(output_dir)

    with StreamDecorator(output_stream).DoneManager( line_prefix='', 
                                                     done_prefix="\nTotal execution time: ",
                                                     done_suffix='\n',
                                                   ) as dm:
        temp_filename = Shell.GetEnvironment().CreateTempFilename(binary_ext)
        with CallOnExit(lambda: os.remove(temp_filename)):
            # Download the file
            progress = [ None, 0, ]

            # ----------------------------------------------------------------------
            def Callback(count, block_size, total_size):
                if progress[0] == None:
                    progress[0] = tqdm.tqdm( total=total_size,
                                             desc="Downloading",
                                             unit=" bytes",
                                             mininterval=0.5,
                                             leave=True,
                                           )

                else:
                    assert count, block_size

                    current = min(count * block_size, total_size)
                    assert current >= progress[1]

                    progress[0].update(current - progress[1])
                    progress[1] = current

            # ----------------------------------------------------------------------
            
            result = six.moves.urllib.request.urlretrieve(url, temp_filename, reporthook=Callback)
            progress[0].close()

            # Extract the file
            os.makedirs(output_dir)

            with zipfile.ZipFile(temp_filename) as zf:
                total_bytes = sum((f.file_size for f in zf.infolist()))
                
                with tqdm.tqdm( total=total_bytes,
                                desc="Extracting",
                                unit=" bytes",
                                mininterval=0.5,
                                leave=True,
                              ) as progress:
                    for f in zf.infolist():
                        try:
                            zf.extract(f, output_dir)

                            if f.file_size:
                                progress.update(f.file_size)
                        except:
                            output_stream.write("WARNING: Unable to extract '{}'.\n".format(f.filename))

            # Write the unique_id (if necessary)
            if unique_id:
                with open(os.path.join(output_dir, UNIQUE_ID_FILENAME), 'w') as f:
                    f.write(unique_id)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
