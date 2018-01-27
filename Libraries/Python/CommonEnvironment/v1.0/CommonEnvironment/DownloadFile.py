# ----------------------------------------------------------------------
# |  
# |  DownloadFile.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-01-26 08:30:56
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import shutil
import sys

import six
import tqdm

from CommonEnvironment import ModifiableValue
from CommonEnvironment import FileSystem
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

def DownloadFile(url, dest_filename, output_stream):
    with StreamDecorator(output_stream).SingleLineDoneManager( "Downloading '{}'...".format(url),
                                                             ) as dm:
        # ----------------------------------------------------------------------
        class Status(object):
            
            # ----------------------------------------------------------------------
            def __init__(self, total_size):
                self._progress_bar          = tqdm.tqdm( file=output_stream,
                                                         total=total_size,
                                                         desc="Downloading",
                                                         unit=" bytes",
                                                         mininterval=0.5,
                                                         leave=False,
                                                         ncols=120,
                                                       )
                self._current               = 0
                self._total                 = total_size

            # ----------------------------------------------------------------------
            def Update(self, count, block_size, total_size):
                assert count, block_size

                current = min(count * block_size, total_size)
                
                assert current >= self._current
                self._progress_bar.update(current - self._current)

                self._current = current

            # ----------------------------------------------------------------------
            def Close(self):
                assert self._progress_bar is not None
                self._progress_bar.close()

                self._progress_bar = None

            # ----------------------------------------------------------------------
            def WasSuccessful(self):
                return self._current == self._total

        # ----------------------------------------------------------------------

        status = ModifiableValue(None)

        # ----------------------------------------------------------------------
        def Callback(count, block_size, total_size):
            if status.value is None:
                status.value = Status(total_size)
            else:
                status.value.Update(count, block_size, total_size)

        # ----------------------------------------------------------------------

        temp_filename = Shell.GetEnvironment().CreateTempFilename()

        six.moves.urllib.request.urlretrieve(url, temp_filename, reporthook=Callback)
        status.value.Close()

        dm.result = 0 if status.value.WasSuccessful() else -1

        FileSystem.MakeDirs(os.path.dirname(dest_filename))
        os.rename(temp_filename, dest_filename)

        return dm.result
