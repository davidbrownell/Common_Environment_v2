# ---------------------------------------------------------------------------
# |  
# |  StreamDecorator.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/09/2015 12:03:52 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import sys
import textwrap

from contextlib import contextmanager
from six import StringIO

from . import ModifiableValue, Any
from .TimeDelta import TimeDelta

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class StreamDecorator(object):
    """\
    Decorates the provided stream.
    """

    # ----------------------------------------------------------------------
    # |  Public Methods
    def __init__( self,
                  stream_or_streams,
                  line_prefix='',           # string or def Func(column) -> string
                  line_suffix='',           # string or def Func(column) -> string
                  prefix='',                # string or def Func(column) -> string
                  suffix='',                # string or def Func(column) -> string
                  one_time_prefix='',       # string or def Func(column) -> string
                  one_time_suffix='',       # string or def Func(column) -> string
                  tab_length=4,
                  skip_first_line_prefix=False,
                  is_associated_stream=False,
                ):
        self._streams                       = stream_or_streams if isinstance(stream_or_streams, list) else [ stream_or_streams, ] if stream_or_streams != None else []
        self._line_prefix                   = line_prefix if callable(line_prefix) else lambda column: line_prefix
        self._line_suffix                   = line_suffix if callable(line_suffix) else lambda column: line_suffix
        self._prefix                        = prefix if callable(prefix) else lambda column: prefix
        self._suffix                        = suffix if callable(suffix) else lambda column: suffix
        self._one_time_prefix               = one_time_prefix if callable(one_time_prefix) else lambda column: one_time_prefix
        self._one_time_suffix               = one_time_suffix if callable(one_time_suffix) else lambda column: one_time_suffix
        self._tab_length                    = tab_length

        self._displayed_one_time_prefix     = False
        self._displayed_one_time_suffix     = False
        self._displayed_prefix              = False
        self._skip_first_line_prefix        = skip_first_line_prefix

        self._column                        = 0
        self._indent_stack                  = []

        self.IsSet                          = Any(self._streams, lambda stream: stream and getattr(stream, "IsSet", True))
        self.IsAssociatedStream             = is_associated_stream or Any(self._streams, lambda stream: stream and getattr(stream, "IsAssociatedStream", False))

    # ---------------------------------------------------------------------------
    def write(self, content, custom_line_prefix=''):
        if not self._streams or not content:
            return self

        # ---------------------------------------------------------------------------
        def Impl(content, eol=None):
            if self._column == 0:
                if self._skip_first_line_prefix:
                    self._skip_first_line_prefix = False
                else:
                    self.write_raw(self._line_prefix(self._column))

                    if custom_line_prefix:
                        self.write_raw(custom_line_prefix)

            self.write_raw(content)
            self._column += len(content) + (content.count('\t') * (self._tab_length - 1))

            if eol:
                self.write_raw(self._line_suffix(self._column))
                self.write_raw(eol)

                self._column = 0

        # ---------------------------------------------------------------------------
        
        if not self._displayed_one_time_prefix:
            self.write_raw(self._one_time_prefix(self._column))
            self._displayed_one_time_prefix = True

        if not self._displayed_prefix:
            self.write_raw(self._prefix(self._column))
            self._displayed_prefix = True

        while True:
            match = self._eol_regex.search(content)
            if not match:
                break

            Impl(content[:match.start()], eol=match.group("eol"))
            content = content[match.end():]

        if content:
            Impl(content)

        return self

    # ---------------------------------------------------------------------------
    def write_raw(self, content):
        for stream in self._streams:
            stream.write(content)

        return self

    # ---------------------------------------------------------------------------
    def flush(self, force_suffix=False):
        if not self._streams:
            return self

        if force_suffix or self._column != 0:
            suffix = self._line_suffix(self._column)

            for stream in self._streams:
                stream.write(suffix)
                stream.write(self._suffix(self._column))

            self._displayed_prefix = False
        
        if not self._displayed_one_time_suffix:
            for stream in self._streams:
                stream.write(self._one_time_suffix(self._column))

            self._displayed_one_time_suffix = True

        self._column = 0
            
        return self

    # ----------------------------------------------------------------------
    @contextmanager
    def DoneManager( self,
                     
                     line_prefix="  ",

                     done_prefix='',                    # Can be a string or functor, def Func() -> string
                     done_suffix='',                    # Can be a string or functor, def Func() -> string
                     done_suffix_functor=None,          # Can be functor or list, def Func() -> string

                     done_result=True,                  # Display the result
                     done_time=True,                    # Display the time delta

                     display_exceptions=True,           # Will display the exception if True
                     display_exception_callstack=True,  # Will display the exception with a callstack if True
                     suppress_exceptions=False,         # Will not propigate the exception if True

                     associated_stream=None,
                     associated_streams=None,           # Streams that should be adjusted in conjunction with this stream. Most of the time, this is used
                                                        # to manage verbose streams that are aligned with status streams, where the status stream is self
                                                        # and the verbose stream content is interleaved with it.
                                                        #
                                                        # Example:
                                                        #     import sys
                                                        #
                                                        #     from StringIO import StringIO 
                                                        #     from CommonEnvironment.StreamDecorator import StreamDecorator
                                                        #
                                                        #     sink = StringIO()
                                                        #     
                                                        #     verbose_stream = StreamDecorator(sink)
                                                        #     status_stream = StreamDecorator([ sys.stdout, verbose_stream, ])
                                                        #     
                                                        #     status_stream.write("0...")
                                                        #     with status_stream.DoneManager(associated_stream=verbose_stream) as ( dm1, verbose_stream1 ):
                                                        #         verbose_stream1.write("Verbose 0\n----")
                                                        #     
                                                        #         dm1.stream.write("1...")
                                                        #         with dm1.stream.DoneManager(associated_stream=verbose_stream1) as ( dm2, verbose_stream2 ):
                                                        #             verbose_stream2.write("Verbose 1\n----")
                                                        #     
                                                        #             dm2.stream.write("2...")
                                                        #             with dm2.stream.DoneManager(associated_stream=verbose_stream2) as ( dm3, verbose_stream3 ):
                                                        #                 verbose_stream3.write("Verbose 2\n----")
                                                        #     
                                                        #                 dm3.stream.write("3...")
                                                        #                 with dm3.stream.DoneManager(associated_stream=verbose_stream3) as ( dm4, verbose_stream4 ):
                                                        #                     verbose_stream4.write("Verbose 3\n----")
                                                        #                     verbose_stream4.flush() 
                                                        #     
                                                        #     sys.stdout.write("\n**\n{}\n**\n".format(sink.getvalue()))
                   ):
        done_suffix_functors = done_suffix_functor if isinstance(done_suffix_functor, list) else [ done_suffix_functor, ]

        start_time = TimeDelta()

        done_prefix = [ done_prefix, ]
        done_suffix = [ done_suffix, ]

        # ----------------------------------------------------------------------
        class Info(object):
            def __init__(self, stream, result=0):
                self.stream                 = stream
                self.result                 = result

                self.stream._parent_info = self         # <Access to a protected member of a client class> pylint: disable = W0212

        # ----------------------------------------------------------------------
        
        info = Info(StreamDecorator( self,
                                     one_time_prefix='\n' if line_prefix else '',
                                     line_prefix=line_prefix,
                                   ))

        # ----------------------------------------------------------------------
        def Cleanup():
            assert info.result != None

            suffixes = []

            if done_result:
                suffixes.append(str(info.result))

            if done_time:
                suffixes.append(start_time.CalculateDelta(as_string=True))

            for dsf in done_suffix_functors:
                if not dsf:
                    continue

                result = dsf()
                if result != None:
                    suffixes.append(result)

            if not isinstance(done_prefix[0], basestring):
                done_prefix[0] = done_prefix[0]()
            
            if not isinstance(done_suffix[0], basestring):
                done_suffix[0] = done_suffix[0]()

            if suffixes:
                content = ', '.join(suffixes)

                if done_prefix[0].strip():
                    # Custom Prefix
                    content = "({})".format(content)
                elif not line_prefix:
                    # Used to show composite results
                    pass
                else:
                    # Single-line results
                    content = "DONE! ({})".format(content)
            else:
                content = ''

            self.write("{prefix}{content}{suffix}\n" \
                            .format( prefix=done_prefix[0],
                                     content=content,
                                     suffix=done_suffix[0],
                                   ))
            self.flush()

            # Propagate the result
            if info.result != 0:
                stream = self

                while hasattr(stream, "_parent_info"):
                    if stream._parent_info.result != 0:                     # <Access to a protected member of a client class> pylint: disable = W0212, E1101
                        break

                    stream._parent_info.result = info.result                # <Access to a protected member of a client class> pylint: disable = W0212, E1101
                    stream = stream._parent_info.stream                     # <Access to a protected member of a client class> pylint: disable = W0212, E1101

        # ----------------------------------------------------------------------
        
        from .CallOnExit import CallOnExit

        with CallOnExit(Cleanup):
            try:
                if associated_stream:
                    if not associated_streams:
                        associated_streams = []

                    associated_streams.append(associated_stream)

                if not associated_streams:
                    yield info
                else:
                    yield tuple([ info, ] + [ StreamDecorator( stream,
                                                               line_prefix=' ' * len(line_prefix),
                                                               one_time_prefix='\n',
                                                               one_time_suffix="\n<flush>",
                                                               is_associated_stream=True,
                                                             )
                                              for stream in associated_streams
                                            ])

                if info.result == None:
                    info.result = 0

            except Exception:
                if info.result in [ None, 0, ]:
                    info.result = -1

                if display_exceptions:
                    ex = sys.exc_info()[1]

                    if ( not getattr(ex, "_DisplayedException", False) and
                         not getattr(info.stream, "IsAssociatedStream", False)
                       ):
                        ex._DisplayedException = True
                        
                        if display_exception_callstack:
                            import traceback
                            info.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify(traceback.format_exc(), len("ERROR: ")).rstrip()))
                        else:
                            info.stream.write("ERROR: {}\n".format(str(ex).rstrip()))

                if not suppress_exceptions:
                    raise

    # ---------------------------------------------------------------------------
    @classmethod
    def LeftJustify( cls, 
                     content, 
                     starting_col=4, 
                     skip_first_line=True,
                     add_suffix=False,
                   ):
        whitespace_prefix = ' ' * starting_col
        
        sink = StringIO()
        decorator = cls( sink, 
                         line_prefix=whitespace_prefix, 
                         skip_first_line_prefix=skip_first_line,
                       )

        decorator.write(content)
        decorator.flush()

        result = sink.getvalue()

        if add_suffix:
            result += whitespace_prefix

        return result

    # ---------------------------------------------------------------------------
    @classmethod
    def Wrap(cls, content, cols=80):
        if not content:
            return ''

        content = '\n'.join([ line.lstrip() for line in content.split('\n') ])

        looks_like_a_list_regexes = [ # - Foo
                                      # * Bar
                                      # _ Baz
                                      re.compile(r"^[_\-\*]\s*\S.*$"),

                                      # one : two
                                      # foo - bar
                                      # a _ b
                                      re.compile(r"^\S.*?[_\:\-]\s*\S.*$"),
                                    ]

        paragraphs = []
        for paragraph in content.split('\n\n'):
            lines = paragraph.split('\n')

            # Look for a collection of lines that look like a list ("look like a list" is subjective, but 
            # give it our best shot).
            is_a_list = True
            
            for line in lines:
                if not line:
                    continue

                found = False
                for regex in looks_like_a_list_regexes:
                    if regex.match(line):
                        found = True
                        break

                if not found:
                    is_a_list = False
                    break

            if is_a_list:
                paragraphs.append('\n'.join([ "    {}".format(line) for line in lines ]))
            else:
                paragraphs.append(textwrap.fill(paragraph, cols))

        return '\n\n'.join(paragraphs)
        
    # ----------------------------------------------------------------------
    # |  Private Data
    _eol_regex = re.compile(r"(?P<eol>\r?\n)")
    