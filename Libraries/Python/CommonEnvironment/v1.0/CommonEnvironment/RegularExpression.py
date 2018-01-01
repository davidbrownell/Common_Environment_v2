# ---------------------------------------------------------------------------
# |  
# |  RegularExpression.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/13/2015 07:37:00 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Tools and utilities that help when working with regular expressions.
"""

import itertools
import os
import re
import sys

import six

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
OldSchoolTemplateStringTagRegex             = re.compile(r"%\((?P<tag>.+?)\).*?(?P<type>[sdf])")
TemplateStringTagRegex                      = re.compile(r"\{\s*(?P<tag>.+?)(?:\:.*?(?P<type>[df])?)?\s*\}")

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def TemplateStringToRegex( content,
                           optional_tags=None,          # []
                           tag_regex=None,              # TemplateStringTagRegex
                           as_string=False,
                           match_whole_string=True,
                         ):
    newline_tag = "__<<!!??Newline??!!>>__"
    whitespace_tag = "__<<!!??Whitespace??!!>>__"

    optional_tags = optional_tags or []
    tag_regex = tag_regex or TemplateStringTagRegex

    # Convert all placeholders in the template string to regular expressions
    
    # Extract newlines and replace them later.
    content = re.sub( r"\r?\n",
                      lambda match: newline_tag,
                      content,
                      re.DOTALL | re.MULTILINE,
                    )
    
    # Extract long whitespace sequences
    content = re.sub( r"\s\s+",
                      lambda match: whitespace_tag,
                      content,
                      re.DOTALL | re.MULTILINE,
                    )

    output = []
    prev_index = 0
    found_tags = []

    for match in tag_regex.finditer(content):
        # Escape everything before this match
        output.append(re.escape(content[prev_index : match.start()]))

        # Modify the match
        tag = match.group("tag")
        type_ = match.group("type") or 's'

        if type_ == 's':
            type_ = "."
        elif type_ == 'd':
            type_ = r"\d"
        elif type_ == 'f':
            type_ = r"[\d\.]"
        else:
            assert False, type_

        if tag in found_tags:
            output.append("(?P={})".format(tag))
        else:
            found_tags.append(tag)
            output.append("(?P<{tag}>{type_}{arity}?)".format( tag=tag,
                                                               type_=type_,
                                                               arity='*' if tag in optional_tags else '+',
                                                             ))

        prev_index = match.end()

    output.append(re.escape(content[prev_index :]))
    
    output = ''.join(output)
    
    if match_whole_string:
        output = "^{}$".format(output)

    # Repace newlines and whitespace
    for tag, replacement in [ ( newline_tag, r"\r?\n" ),
                              ( whitespace_tag, r"\s+" ),
                            ]:
        output = output.replace(re.escape(tag), replacement)

    output = output.replace(r"\ ", ' ')
    
    if as_string:
        return output

    return re.compile(output, re.DOTALL | re.MULTILINE)

# ---------------------------------------------------------------------------
def PythonToJavaScript(regex_string):
    """\
    Converts a python regular expression string to its JavaScript counterpart.
    """

    for expr, sub in [ ( re.compile(r"\(\?#.+?\)", re.MULTILINE | re.DOTALL), lambda match: '' ),
                       ( re.compile(r"\(?P<.+?>", re.MULTILINE | re.DOTALL), lambda match: '(' ),
                     ]:
        regex_string = expr.sub(sub, regex_string)

    return regex_string

# ----------------------------------------------------------------------
def WildcardSearchToRegularExpression( value,
                                       as_string=False,
                                     ):
    value = re.escape(value)

    for source, dest in [ ( r"\*", ".*" ),
                          ( r"\?", "." ),
                        ]:
        value = value.replace(source, dest)

    value = "^{}$".format(value)

    if as_string:
        return value

    return re.compile(value)

# ----------------------------------------------------------------------
def Generate( regex_or_regex_string, 
              content, 
              yield_prefix=False,
            ):
    # Handles some of the wonkiness associated with re.split.

    if isinstance(regex_or_regex_string, six.string_types):
        regex = re.compile(regex_or_regex_string)
    else:
        regex = regex_or_regex_string

    items = regex.split(content)
    if len(items) > 1:
        # Ignore the initial item, as that will be everything that comes before
        # the first match (or None if the match is at the beginning of the content).
        if yield_prefix:
            yield { "_data_" : items[0] or '', }

        items = items[1:]

        if regex.groups:
            if regex.groups == 1:
                MatchDecorator = lambda match: (match, )
            else:
                MatchDecorator = lambda match: match

            # We have capture values.
            for index in six.moves.range(0, len(items), 2):
                match = MatchDecorator(items[index])
                data = items[index + 1]

                result = { k : v for k, v in six.moves.zip(six.iterkeys(regex.groupindex), match) }
                result["_data_"] = data

                yield result

        else:
            for item in items:
                yield { "_data_" : item,
                      }
