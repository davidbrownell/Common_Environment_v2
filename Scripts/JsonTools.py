# ----------------------------------------------------------------------
# |  
# |  XmlToJson.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-02-02 15:55:11
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Various tools that help when working with JSON content.
"""

import json
import os
import re
import sys

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint( key_attribute_name=CommandLine.EntryPoint.ArgumentInfo("Attribute name to use as the key"),
                         parent_attribute_name=CommandLine.EntryPoint.ArgumentInfo("Attribute name to use as the parent"),
                         input=CommandLine.EntryPoint.ArgumentInfo("Input filename or content"),
                         output=CommandLine.EntryPoint.ArgumentInfo("Output filename or 'stdout'"),
                         child_attribute_name=CommandLine.EntryPoint.ArgumentInfo("Attribute name to use as the child"),
                       )
@CommandLine.FunctionConstraints( key_attribute_name=CommandLine.StringTypeInfo(),
                                  parent_attribute_name=CommandLine.StringTypeInfo(),
                                  input=CommandLine.StringTypeInfo(),
                                  output=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def ToHierarchy( key_attribute_name,
                 parent_attribute_name,
                 input,
                 output,
                 child_attribute_name="children",
                 pretty_print=False,
                 output_stream=sys.stdout,
               ):
    """\
    Converts from a flat JSON hierarchy to a nested one, where nesting is controlled by
    <key_attribute_name>, <parent_attribute_name>, and <child_attribute_name>.

        key_attribute_name      - unique identifier that is valid for all items
        parent_attribute_name   - existing identifier that uniquely points to an item's parent
        child_attribute_name    - attribute created on each item that contains all child attributes
    """

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nComplete Result: ",
                                                   ) as dm:
        if os.path.isfile(input):
            input = open(input).read()

        input = json.loads(input)
        if isinstance(input, dict) and len(input) == 1 and isinstance(input.values()[0], list):
            input = input.values()[0]

        lookup = {}
    
        # Get the items
        dm.stream.write("Processing items...")
        with dm.stream.DoneManager() as this_dm:
            for index, item in enumerate(input):
                if key_attribute_name not in item:
                    this_dm.stream.write("ERROR: Item {} does not have the attribute '{}'.\n".format(index + 1, key_attribute_name))
                    this_dm.result = -1

                    continue

                key = item[key_attribute_name]

                if child_attribute_name in item:
                    this_dm.stream.write("ERROR: '{}' already has the key '{}'.\n".format(key, child_attribute_name))
                    this_dm.result = -1

                    continue

                item[child_attribute_name] = []

                lookup[key] = item
                
            if this_dm.result != 0:
                return this_dm.result

        # Get the associations
        root_items = []

        dm.stream.write("Processing hierarchy...")
        with dm.stream.DoneManager() as this_dm:
            for index, item in enumerate(input):
                has_parent = False

                if parent_attribute_name in item:
                    key = item[key_attribute_name]
                    parent = item[parent_attribute_name]

                    if parent in lookup:
                        lookup[parent][child_attribute_name].append(item)
                        has_parent = True

                if not has_parent:
                    root_items.append(item)

        dm.stream.write("Generating output...")
        with dm.stream.DoneManager() as this_dm:
            if pretty_print:
                result = json.dumps(root_items, indent=2, separators=[ ', ', ' : ', ])
            else:
                result = json.dumps(root_items)
            
            if output == "stdout":
                this_dm.stream.write(result)
            else:
                with open(output, 'w') as f:
                    f.write(result)
    
        return dm.result    

# ----------------------------------------------------------------------
@CommandLine.EntryPoint( key_attribute_name=CommandLine.EntryPoint.ArgumentInfo("Attribute name to use as the key"),
                         child_attribute_name=CommandLine.EntryPoint.ArgumentInfo("Attribute name that is used to identify the item's children"),
                         input=CommandLine.EntryPoint.ArgumentInfo("Input filename or content"),
                         output=CommandLine.EntryPoint.ArgumentInfo("Output filename or 'stdout'"),
                         hierarchy_attribute_name=CommandLine.EntryPoint.ArgumentInfo("Attribute name created on each item")
                       )
@CommandLine.FunctionConstraints( key_attribute_name=CommandLine.StringTypeInfo(),
                                  child_attribute_name=CommandLine.StringTypeInfo(),
                                  input=CommandLine.StringTypeInfo(),
                                  output=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def Flatten( key_attribute_name, 
             child_attribute_name,
             input,
             output,
             hierarchy_attribute_name="hierarchy",
             pretty_print=False,
             output_stream=sys.stdout,
           ):
    """\
    Flattens a JSON hierarchy, where flattening is controlled by
    <key_attribute_name>, <child_attribute_name>, and <hierarchy_attribute_name>.

        key_attribte_name           - unique identifier that is valid for all items
        child_attribute_name        - attribute name for each item that identifies its children
        hierarchy_attribute_name    - attribute created on each item that contains the original hierarchial data
    """

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nComplete Results: ",
                                                   ) as dm:
        if os.path.isfile(input):
            input = open(input).read()

        input = json.loads(input)
        if isinstance(input, dict) and len(input) == 1 and isinstance(input.values()[0], list):
            input = input.values()[0]
            
        # Process the input
        results = []

        dm.stream.write("Processing items...")
        with dm.stream.DoneManager() as this_dm:

            # ----------------------------------------------------------------------
            def Impl(item, stack):
                if key_attribute_name not in item:
                    this_dm.stream.write("ERROR: The attribute '{}' does not exist for the item '{}'.\n".format(key_attribute_name, item))
                    this_dm.result = -1

                    return

                key = item[key_attribute_name]

                if hierarchy_attribute_name in item:
                    this_dm.stream.write("ERROR: The attribute '{}' is already in '{}'.\n".format(hierarchy_attribute_name, key))
                    this_dm.result = -1

                    return
                
                item[hierarchy_attribute_name] = '/'.join(stack + [ key, ])
                results.append(item)

                if child_attribute_name in item:
                    stack.append(key)
                    with CallOnExit(stack.pop):
                        for child in item[child_attribute_name]:
                            Impl(child, stack)

                    del item[child_attribute_name]

            # ----------------------------------------------------------------------
            
            for item in input:
                Impl(item, [])

            if this_dm.result != 0:
                return this_dm.result

        dm.stream.write("Generating output...")
        with dm.stream.DoneManager() as dm:
            if pretty_print:
                result = json.dumps(results, indent=2, separators=[ ', ', ' : ', ])
            else:
                result = json.dumps(results)

            if output == "stdout":
                this_dm.stream.write(result)
            else:
                with open(output, 'w') as f:
                    f.write(result)

        return dm.result
    
# ----------------------------------------------------------------------
@CommandLine.EntryPoint( input=CommandLine.EntryPoint.ArgumentInfo("Input filename or content"),
                         output=CommandLine.EntryPoint.ArgumentInfo("Output filename or 'stdout'"),
                       )
@CommandLine.FunctionConstraints( input=CommandLine.StringTypeInfo(),
                                  output=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def FromXML( input,
             output,
             pretty_print=False,
             output_stream=sys.stdout,
           ):
    """\
    Convert from XML to JSON
    """

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nComposite Result: ",
                                                   ) as dm:
        from xml.etree import cElementTree as ET

        if os.path.isfile(input):
            with open(input) as f:
                content = f.read()
        else:
            content = input

        # TODO: This should use a SAX parser
        namespace_regex = re.compile(r"^(?P<namespace>\{\S+\})?(?P<tag>.+?)$")

        # ----------------------------------------------------------------------
        def Parse(element):
            obj = {}

            for k, v in element.attrib.iteritems():
                obj[k] = v

            for child in element.getchildren():
                if not isinstance(child.tag, basestring):
                    continue

                child_obj = Parse(child)
                child_obj = child_obj or None

                match = namespace_regex.match(child.tag)
                assert match, child.tag

                tag = match.group("tag")
                
                if tag in obj:
                    if not isinstance(obj[tag], list):
                        obj[tag] = [ obj[tag], ]

                    obj[tag].append(child_obj)
                else:
                    obj[tag] = child_obj

            text = (element.text or '').strip()
            if text:
                if not obj:
                    return text

                obj[None] = text

            return obj

        # ----------------------------------------------------------------------
        
        obj = Parse(ET.fromstring(content))

        if pretty_print:
            result = json.dumps(obj, indent=2, separators=[ ', ', ' : ', ])
        else:
            result = json.dumps(obj)
        
        if output == "stdout":
            dm.stream.write(result)
        else:
            with open(output, 'w') as f:
                f.write(result)

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
