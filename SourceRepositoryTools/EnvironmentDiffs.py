# ----------------------------------------------------------------------
# |  
# |  EnvironmentDiffs.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-19 14:41:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Displays differenced between this activated environment and the original environment.
"""

import json
import os
import sys
import textwrap

import six

from CommonEnvironment import CommandLine

from SourceRepositoryTools.Impl.ActivationData import ActivationData

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_stream=None,
                                )
def EntryPoint( output_stream=sys.stdout,
                decorate=False,
              ):
    original_env = ActivationData.Load(None, None).OriginalEnvironment
    this_env = dict(os.environ)

    differences = {}

    for k, v in six.iteritems(this_env):
        if ( k not in original_env or
             original_env[k] != v
           ):
            differences[k] = v

    if decorate:
        output_stream.write(textwrap.dedent(
            """\
            --------------------------------------------------------------------------------
            {}
            --------------------------------------------------------------------------------
            """).format(json.dumps(differences)))
    else:
        json.dump(differences, output_stream)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass