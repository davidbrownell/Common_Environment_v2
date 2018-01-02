# ---------------------------------------------------------------------------
# |  
# |  UpdateVersion.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  01/10/2016 08:32:44 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Updates a version string
"""

import os
import re
import sys
import textwrap
import time

from collections import OrderedDict

import six

from CommonEnvironment import CommandLine
from CommonEnvironment import RegularExpression
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
def _CreatePython(*args, **kwargs): return __CreatePython(*args, **kwargs)
def _UpdatePython(*args, **kwargs): return __UpdatePython(*args, **kwargs)
def _CreateWindows(*args, **kwargs): return __CreateWindows(*args, **kwargs)
def _UpdateWindows(*args, **kwargs): return __UpdateWindows(*args, **kwargs)

# ---------------------------------------------------------------------------
EXTENSION_MAP = OrderedDict([ ( ".py", ( _CreatePython, _UpdatePython ) ),
                              ( ".win.h", (_CreateWindows, _UpdateWindows ) ),
                            ])

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( filename=CommandLine.FilenameTypeInfo(ensure_exists=False),
                                  major_version=CommandLine.IntTypeInfo(min=0),
                                  minor_version=CommandLine.IntTypeInfo(min=0),
                                  additional_data=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                                  output_stream=None,
                                )
def Create( filename,
            major_version,
            minor_version,
            additional_data=None,
            output_stream=sys.stdout,
          ):
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    func = None

    for k, v in six.iteritems(EXTENSION_MAP):
        if filename.endswith(k):
            func = v[0]
            break

    if func == None:
        raise CommandLine.UsageException("'{}' is not  a supported file type; supported extensions are {}".format( filename, 
                                                                                                                   ', '.join([ "'{}'".format(k) for k in six.iterkeys(EXTENSION_MAP) ]),
                                                                                                                 ))

    output_stream.write("Writing '{}'...".format(filename))
    with StreamDecorator(output_stream).DoneManager() as dm:
        content = func(major_version, minor_version, _GetJulian(), 0, additional_data)
        with open(filename, 'w') as f:
            f.write(content)

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( filename=CommandLine.FilenameTypeInfo(),
                                  output_stream=None,
                                )
def Update( filename,
            in_place=False,
            reset_build_number=False,
            output_stream=sys.stdout,
          ):
    func = None

    for k, v in six.iteritems(EXTENSION_MAP):
        if filename.endswith(k):
            func = v[1]
            break

    if func == None:
        raise CommandLine.UsageException("'{}' is not  a supported file type; supported extensions are {}".format( filename, 
                                                                                                                   ', '.join([ "'{}'".format(k) for k in six.iterkeys(EXTENSION_MAP) ]),
                                                                                                                 ))

    content = func( open(filename).read(), 
                    _GetJulian(),
                    False if reset_build_number else True,
                  )

    if in_place:
        output_stream.write("Overwriting '{}'...".format(filename))
        with StreamDecorator(output_stream).DoneManager() as dm:
            with open(filename, 'w') as f:
                f.write(content)
    else:
        output_stream.write(content)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _GetJulian():
    t = time.localtime()
    return (t[0] % 100) * 1000 + t[7]

# ---------------------------------------------------------------------------
def __CreatePython( major_version,
                    minor_version,
                    julian,
                    build,
                    additional_data,
                  ):
    output = []

    output.append(textwrap.dedent(
        """\
        # This file was generated by '{}' on '{}' - Please do not modify this file as any
        # custom changes will be overwritten during future generations.

        """).format(_script_name, time.asctime()))

    output.append('VERSION = "{major}.{minor:02}.{julian:05}.{build}"\n\n'.format( major=major_version,
                                                                                   minor=minor_version,
                                                                                   julian=julian,
                                                                                   build=build,
                                                                                 ))
    output.append('\n'.join([ '{} = {}'.format(k, v) for k, v in six.iteritems(additional_data) ]))

    return "{}\n".format('\n'.join(output))

# ---------------------------------------------------------------------------
def __UpdatePython( content,
                    julian,
                    should_inc_build,
                  ):
    regex = re.compile( textwrap.dedent(
                           r"""(?#
                            VERSION     )^VERSION\s*=\s*"(?P<version>(?#
                              major     )(?P<major>\d+)\.(?#
                              minor     )(?P<minor>\d+)\.(?#
                              julian    )(?P<julian>\d+)\.(?#
                              build     )(?P<build>\d+)(?#
                                        ))"(?#
                            )"""),
                        re.DOTALL | re.MULTILINE,
                      )

    # ---------------------------------------------------------------------------
    def ReplaceFunc(match):
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        prev_julian = int(match.group("julian"))
        build = int(match.group("build"))

        if julian != prev_julian or not should_inc_build:
            build = 0
        else:
            build += 1

        return 'VERSION = "{major}.{minor:02}.{julian:05}.{build}"'.format( major=major,
                                                                            minor=minor,
                                                                            julian=julian,
                                                                            build=build,
                                                                          )

    # ---------------------------------------------------------------------------
    
    new_content, num_matches = regex.subn(ReplaceFunc, content)
    if num_matches == 0:
        raise Exception(textwrap.dedent(
            """\
            No matches were found. Please ensure that the following statement appears within the file:

                VERSION = <major>.<minor>.<julian>.<build>
                
            """))

    return new_content

# ---------------------------------------------------------------------------
_WINDOWS_TEMPLATE = textwrap.dedent(
    """\
    #define MAJOR_VERSION           {major}
    #define MINOR_VERSION           {minor}
    #define JULIAN_VERSION          {julian}
    #define BUILD_VERSION           {build}
    
    #define MAJOR_VERSION_STRING    "{major}"
    #define MINOR_VERSION_STRING    "{minor}"
    #define JULIAN_VERSION_STRING   "{julian}"
    #define BUILD_VERSION_STRING    "{build}"
    
    #define FILE_VERSION            MAJOR_VERSION,MINOR_VERSION,JULIAN_VERSION,BUILD_VERSION
    #define PRODUCT_VERSION         FILE_VERSION
    
    #define FILE_VERSION_STRING     MAJOR_VERSION_STRING "." MINOR_VERSION_STRING "." JULIAN_VERSION_STRING "." BUILD_VERSION_STRING
    #define PRODUCT_VERSION_STRING  FILE_VERSION_STRING
    """)

def __CreateWindows( major_version,
                     minor_version,
                     julian,
                     build,
                     additional_data,
                   ):
    return _WINDOWS_TEMPLATE.format( major=major_version,
                                     minor=minor_version,
                                     julian=julian,
                                     build=build,
                                   )

# ---------------------------------------------------------------------------
def __UpdateWindows( content,
                     julian,
                     should_inc_build,
                   ):
    match = re.match(RegularExpression.TemplateStringToRegex(_WINDOWS_TEMPLATE), content, re.DOTALL | re.MULTILINE)
    assert match

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    prev_julian = int(match.group("julian"))
    build = int(match.group("build"))

    if julian != prev_julian or not should_inc_build:
        build = 0
    else:
        build += 1

    return _WINDOWS_TEMPLATE.format( major=major,
                                     minor=minor,
                                     julian=julian,
                                     build=build,
                                   )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
