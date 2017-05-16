# ----------------------------------------------------------------------
# |  
# |  UpdateRepositoryIgnoreFile.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-05-14 08:09:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Converts from one registry file format to another.
"""

import os
import re
import sys
import textwrap

from collections import OrderedDict

import inflect
import six

from CommonEnvironment import CommandLine
from CommonEnvironment import Enum
from CommonEnvironment import RegularExpression
from CommonEnvironment import SourceControlManagement
from CommonEnvironment.StreamDecorator import FunctionToStreamWrapper, StreamDecorator
from CommonEnvironment import TaskPool

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect_engine                              = inflect.engine()

# ----------------------------------------------------------------------
def _ReadHg(*args, **kwargs):               return __ReadHg(*args, **kwargs)
def _WriteHg(*args, **kwargs):              return __WriteHg(*args, **kwargs)
def _ReadGit(*args, **kwargs):              return __ReadGit(*args, **kwargs)
def _WriteGit(*args, **kwargs):             return __WriteGit(*args, **kwargs)

# ----------------------------------------------------------------------
SCMS                                        = OrderedDict([ ( scm.Name, scm ) for scm in SourceControlManagement.GetPotentialSCMs() ])

FORMATS                                     = OrderedDict([ ( SCMS["Mercurial"].Name, ( _ReadHg, _WriteHg ) ),
                                                            ( SCMS["Git"].Name, ( _ReadGit, _WriteGit ) ),
                                                          ])

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( code_dir=CommandLine.DirectoryTypeInfo(),
                                  source_format=CommandLine.EnumTypeInfo(list(six.iterkeys(FORMATS))),
                                  dest_format=CommandLine.EnumTypeInfo(list(six.iterkeys(FORMATS))),
                                  output_stream=None,
                                )
def Execute( code_dir,
             source_format,
             dest_format,
             output_stream=sys.stdout,
           ):
    output_stream = StreamDecorator(output_stream)

    output_stream.write("Converting '{}' from '{}' to '{}'...".format( code_dir,
                                                                       source_format,
                                                                       dest_format,
                                                                     ))
    with output_stream.DoneManager():
        FORMATS[dest_format][1](code_dir, FORMATS[source_format][0](code_dir))
        
# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( code_root=CommandLine.DirectoryTypeInfo(),
                                  source_format=CommandLine.EnumTypeInfo(list(six.iterkeys(FORMATS))),
                                  dest_format=CommandLine.EnumTypeInfo(list(six.iterkeys(FORMATS))),
                                  output_stream=None,
                                )
def ExecuteTree( code_root,
                 source_format,
                 dest_format,
                 output_stream=sys.stdout,
               ):
    output_stream = StreamDecorator(output_stream)
    
    output_stream.write('\n')
    with output_stream.DoneManager( line_prefix='',
                                    done_prefix='\nResults: ',
                                    done_suffix='\n',
                                  ) as dm:
        repositories = []

        dm.stream.write("Finding repositories...")
        with dm.stream.DoneManager( done_suffix_functor=lambda: "{} found".format(inflect_engine.no("repository", len(repositories))),
                                  ):
            for scm, root in SourceControlManagement.EnumSCMDirectories(code_root):
                if scm.Name == source_format:
                    repositories.append(root)

        if not repositories:
            return

        # ----------------------------------------------------------------------
        def Invoke(repository, on_status_functor):
            Execute( repository,
                     source_format,
                     dest_format,
                     output_stream=FunctionToStreamWrapper(on_status_functor),
                   )

        # ----------------------------------------------------------------------

        with dm.stream.SingleLineDoneManager( "Generating repositories...",
                                            ) as this_dm:
            TaskPool.Transform( repositories,
                                Invoke,
                                this_dm.stream,
                                name_functor=lambda index, item: item,
                              )

# ----------------------------------------------------------------------
def CommandLineSuffix():
    return StreamDecorator.LeftJustify( textwrap.dedent(
                                            """\
                                            Where available formats are:
                                            {}
                                            """).format('\n'.join([ "    - {}".format(f) for f in six.iterkeys(FORMATS) ])),
                                        4,
                                        skip_first_line=False,
                                      )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
_Type                                       = Enum.Create( "Wildcard",
                                                           "Regex",
                                                         )

# ----------------------------------------------------------------------
def __ReadHg(code_dir):
    scm = SCMS["Mercurial"]

    input_filename = os.path.join(code_dir, scm.IgnoreFilename)
    if not os.path.isfile(input_filename):
        raise Exception("The file '{}' does not exist".format(input_filename))

    with open(input_filename) as f:
        content = f.read()

    results = []

    for match in RegularExpression.Generate( re.compile(r"syntax: (?P<syntax>[^\n]+)\r?\n", re.DOTALL),
                                             content,
                                           ):
        if match["syntax"] == "glob":
            type_ = _Type.Wildcard
        elif match["syntax"] == "regexp":
            type_ = _Type.Regex
        else:
            raise Exception("The syntax type '{}' was not expected".format(match["syntax"]))

        lines = match["_data_"]

        for line in lines.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            results.append(( line, type_ ))

    return results

# ----------------------------------------------------------------------
def __WriteHg(code_dir, content):
    scm = SCMS["Mercurial"]

    other_scm_ignore_expressions = []

    for other_scm in six.itervalues(SCMS):
        if other_scm == scm:
            continue

        other_scm_ignore_expressions += [ "{}/*".format(working_dir) for working_dir in other_scm.WorkingDirectories ]

    with open(os.path.join(code_dir, scm.IgnoreFilename), 'w') as f:
        prev_type = None
        
        for line, type_ in content:
            assert len(scm.WorkingDirectories) == 1, scm.WorkingDirectories
            if line == scm.IgnoreFilename or line.startswith(scm.WorkingDirectories[0]):
                continue

            if type_ != prev_type:
                if type_ == _Type.Wildcard:
                    type_string = "glob"
                elif type_ == _Type.Regex:
                    type_string = "regexp"
                else:
                    assert False, type_

                f.write("{}syntax: {}\n\n".format( '\n' if prev_type != None else '',
                                                   type_string,
                                                 ))

                prev_type = type_

            f.write("{}\n".format(line))

            for index, expr in enumerate(other_scm_ignore_expressions):
                if line == expr:
                    del other_scm_ignore_expressions[index]
                    break

        if other_scm_ignore_expressions:
            f.write('\n'.join(other_scm_ignore_expressions))

# ----------------------------------------------------------------------
def __ReadGit(code_dir):
    input_filename = os.path.join(code_dir, ".gitignore")
    if not os.path.isfile(input_filename):
        raise Exception("The file '{}' does not exist".format(input_filename))

    with open(input_filename) as f:
        content = f.read()

    results = []

    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # TODO: This is not even close to complete (or really even correct)
        results.append(( line, _Type.Wildcard ))

    return results

# ----------------------------------------------------------------------
def __WriteGit(code_dir, content):
    scm = SCMS["Git"]

    other_scm_ignore_expressions = []

    for other_scm in six.itervalues(SCMS):
        if other_scm == scm:
            continue

        other_scm_ignore_expressions += [ "{}/*".format(working_dir) for working_dir in other_scm.WorkingDirectories ]

    with open(os.path.join(code_dir, scm.IgnoreFilename), 'w') as f:
        for line, type_ in content:
            if line == scm.IgnoreFilename or line.startswith(scm.WorkingDirectories[0]):
                continue

            f.write("{}\n".format(line))

            for index, expr in enumerate(other_scm_ignore_expressions):
                if line == expr:
                    del other_scm_ignore_expressions[index]
                    break

        if other_scm_ignore_expressions:
            f.write('\n'.join(other_scm_ignore_expressions))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass