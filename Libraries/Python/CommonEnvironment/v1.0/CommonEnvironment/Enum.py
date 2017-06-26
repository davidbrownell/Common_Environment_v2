# ---------------------------------------------------------------------------
# |  
# |  Enum.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/26/2015 07:18:47 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import hashlib
import inspect
import os
import sys
import textwrap

import six

from .StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

def Create(*values):
    """\
    Dynamically creates an enum-like class with the provided string values.

    Example:
        Color = Create("red", "yellow", "blue", "green")

        c1 = Color.red
        c1.string                           # "red"
        ci.value                            # 0

        Color.IsValid("yellow")             # True
        Color.ToString(Color.blue)          # "blue"

        c2 = Color.FromString("green")
    """

    assert values

    # We need a name that is unique, but stable enough that it will be consistent
    # when minor changes are made to the defining file. Take a hash of the filename
    # and then query a file-specific index to ensure uniqueness. This will remain 
    # stable while enum definitions remain in the same relative order.
    try:
        frame = inspect.stack()[1]
        mod = inspect.getmodule(frame[0])

        calling_filename = mod.__file__
    except:
        calling_filename = "<<Unknown>>"

    index_key = "_CreateEnumClass_%s" % hashlib.sha1(six.b(calling_filename)).hexdigest()
    these_globals = globals()

    if index_key not in these_globals:
        these_globals[index_key] = 0

    class_name = "%s_%s" % (index_key, these_globals[index_key])
    these_globals[index_key] += 1

    statements = textwrap.dedent(
        """\
        {item_statements}

        class {class_name}(object):
            {internal_statements}

            ITEMS                           = [ {comma_delimited_value_names} ]
            STRINGS                         = [ {comma_delimited_value_strings} ]
            VALUES                          = [ {comma_delimited_value_values} ]

            @classmethod
            def IsValid(cls, item):
                return cls._Get(item) != None

            @classmethod
            def ToString(cls, int_value):
                value = cls._Get(int_value)
                if value == None:
                    raise Exception("'%s' is not a valid value" % int_value)

                return value.string

            @classmethod
            def FromString(cls, value):
                value = cls._Get(value)
                if value == None:
                    raise Exception("'%s' is not a valid value" % value)

                return value

            @classmethod
            def FromValue(cls, int_value):
                value = cls._Get(int_value)
                if value == None:
                    raise Exception("'%s' is not a valid value" % int_value)

                return value

            def __init__(self, item=0):
                self._item = None
                self.Item = item
                
            def __iter__(self):
                class Iterator(object):
                    def __init__(self):
                        self._index = 0

                    def next(this_self):
                        if this_self._index < len(self.ITEMS):
                            result = self.ITEMS[this_self._index]
                            this_self._index += 1

                            return result

                        raise StopIteration()

            @property
            def Item(self):
                return self._item  

            @Item.setter
            def Item(self, value):
                self._item = value

            @classmethod
            def _Get(cls, item):
                def CheckByValue(i): return i.value == item
                def CheckByString(i): return i.string == item
                def CheckByItem(i): return i == item

                if isinstance(item, six.string_types):
                    Checker = CheckByString
                elif isinstance(item, int):
                    Checker = CheckByValue
                else:
                    Checker = CheckByItem

                for i in cls.ITEMS:
                    if Checker(i):
                        return i

                return None

        globals()["{class_name}"] = {class_name}
        dynamic_result = {class_name}
        """).format( class_name=class_name,
                     item_statements='\n'.join([ textwrap.dedent(
                                                    # <Wrong hanging indentation> pylint: disable = C0330
                                                    """\
                                                    class {class_name}_{value}Obj(object):
                                                        string              = "{value}"
                                                        value               = {index}
                                                        
                                                        def __str__(self):
                                                            return "{value}"

                                                        def __repr__(self):
                                                            return "{value}"

                                                        def __eq__(self, other):
                                                            if other == None:
                                                                return False

                                                            if isinstance(other, str):
                                                                return self.string == other
                                                            elif isinstance(other, int):
                                                                return self.value == other

                                                            return self.string == other.string and \
                                                                   self.value == other.value

                                                        def __ne__(self, other):
                                                            return not self.__eq__(other)

                                                        def __hash__(self):
                                                            return self.value.__hash__()

                                                    globals()["{class_name}_{value}Obj"] = {class_name}_{value}Obj
                                                    """).format( value=value,
                                                                 index=index,
                                                                 class_name=class_name,
                                                               )
                                                 for index, value in enumerate(values) 
                                               ]),
                     internal_statements=StreamDecorator.LeftJustify('\n'.join([ "{value} = {class_name}_{value}Obj()".format(value=value, class_name=class_name) for value in values ]), 4),
                     comma_delimited_value_names=', '.join(values),
                     comma_delimited_value_strings=', '.join([ '"{}"'.format(value) for value in values ]),
                     comma_delimited_value_values=', '.join([ str(x) for x in six.moves.range(len(values)) ]),
                   )

    l = locals()
    l["dynamic_result"] = None

    exec(statements, globals(), l)          # <Use of exec> pylint: disable = W0122
    return l["dynamic_result"]

