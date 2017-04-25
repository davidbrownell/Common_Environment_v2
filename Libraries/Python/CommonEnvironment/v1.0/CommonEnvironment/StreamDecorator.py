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

import six
from six import StringIO

from contextlib import contextmanager

from CommonEnvironment import ModifiableValue, Any
from CommonEnvironment.TimeDelta import TimeDelta

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  Forwarding Methods
def _InitAnsiSequenceStreamsImpl(*args, **kwargs):      return __InitAnsiSequenceStreamsImpl(*args, **kwargs)
def _GenerateAnsiSequenceStreamImpl(*args, **kwargs):   return __GenerateAnsiSequenceStreamImpl(*args, **kwargs)

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
                  flush_after_write=False,
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
        self._flush_after_write             = flush_after_write
        self._wrote_content                 = False

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
                
            if self._flush_after_write:
                self.flush()

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

        self._wrote_content = True

        return self

    # ---------------------------------------------------------------------------
    def write_raw(self, content):
        for stream in self._streams:
            stream.write(content)

        return self

    # ---------------------------------------------------------------------------
    def flush(self, force_suffix=False):
        if self._streams:
            if force_suffix:
                line_suffix = self._line_suffix(self._column)
                suffix = self._suffix(self._column)
                
                if self._displayed_one_time_suffix:
                    one_time_suffix = ''
                else:
                    one_time_suffix = self._one_time_suffix(self._column)
                    
                for stream in self._streams:
                    stream.write(line_suffix)
                    stream.write(suffix)
                    stream.write(one_time_suffix)
                
                self._displayed_one_time_suffix = True
                
                self._displayed_prefix = False
                self._column = 0
                
            for stream in self._streams:
                stream.flush()
                
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

        info = self._DoneManagerInfo(self, line_prefix)

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

            if not isinstance(done_prefix[0], six.string_types):
                done_prefix[0] = done_prefix[0]()

            if not isinstance(done_suffix[0], six.string_types):
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
                for index, dm in enumerate(info.Enumerate()):
                    if index == 0:
                        continue

                    if dm.result != 0:
                        break
                
                    dm.result = info.result

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

    # ----------------------------------------------------------------------
    @contextmanager
    def SingleLineDoneManager( self, 
                               status,
                               *done_manager_args,
                               **done_manager_kwargs
                             ):
        """\
        Useful when displaying a status message along with
        a progress bar (or other content) that should disappear
        once the activity is complete.

        Only output written via:
            
            - write_verbose
            - write_info
            - write_warning
            - write_error

        will be preserved.
        """

        # <Has no instance of 'member'> pylint: disable = E1101
        dm_ref = ModifiableValue(None)
        reset_line = ModifiableValue(True)

        # ----------------------------------------------------------------------
        def DonePrefix():
            if not reset_line.value:
                # Don't eliminate any data that was displayed
                return "DONE! "
            
            # Move up a line and display the original status message
            # along with the done notification.

            # Try to get the whitespace associated with all parents (if any).
            whitespace_prefix_stack = []

            for index, dm in enumerate(dm_ref.value.Enumerate()):
                if index == 0:
                    continue

                whitespace_prefix_stack.append(dm.stream._line_prefix)

            whitespace_prefix = ''
            while whitespace_prefix_stack:
                whitespace_prefix += whitespace_prefix_stack.pop()(len(whitespace_prefix))

            return "\033[1A\r{}{}DONE! ".format(whitespace_prefix, status)

        # ----------------------------------------------------------------------
        
        self.write(status)
        with self.DoneManager( done_prefix=DonePrefix,
                               *done_manager_args,
                               **done_manager_kwargs
                             ) as dm:
            dm_ref.value = dm
            first_write = ModifiableValue(True)

            # ----------------------------------------------------------------------
            def Write(content, prefix):
                message = "{}: {}\n".format(prefix, content.strip())

                if first_write.value:
                    message = "{}{}".format(dm.stream._line_prefix(0), message)
                    first_write.value = False

                dm.stream.write(message)
                reset_line.value = False

            # ----------------------------------------------------------------------
            
            dm.stream.write_verbose = lambda content: Write(content, "VERBOSE")
            dm.stream.write_info = lambda content: Write(content, "INFO")
            dm.stream.write_warning = lambda content: Write(content, "WARNING")
            dm.stream.write_error = lambda content: Write(content, "ERROR")

            try:
                yield dm
            except:
                reset_line.value = False
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
                                      re.compile(r"^\S.*?\s*[_\:\-]\s*\S.*$"),
                                    ]

        paragraphs = []
        for paragraph in content.split('\n\n'):
            lines = paragraph.split('\n')

            # Look for a collection of lines that look like a list ("looks like a list" is subjective, but 
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
    # Most of the time, users of this module only import this class and not
    # the methods below. Make those methods available here.
    InitAnsiSequenceStreams                 = staticmethod(_InitAnsiSequenceStreamsImpl)
    GenerateAnsiSequenceStream              = staticmethod(_GenerateAnsiSequenceStreamImpl)
    
    # ----------------------------------------------------------------------
    # |  Private Data
    _eol_regex = re.compile(r"(?P<eol>\r?\n)")
    
    # ----------------------------------------------------------------------
    # |  Private Types
    class _DoneManagerInfo(object):

        # ----------------------------------------------------------------------
        def __init__(self, stream_decorator, line_prefix, result=0):
            self.stream                     = StreamDecorator( stream_decorator,
                                                               one_time_prefix='\n' if line_prefix else '',
                                                               line_prefix=line_prefix,
                                                               flush_after_write=True,
                                                             )
            self.result                     = result

            self.stream._done_manager       = self

        # ----------------------------------------------------------------------
        def Enumerate(self):
            # ----------------------------------------------------------------------
            def Impl(decorator):
                for stream in decorator._streams:
                    if hasattr(stream, "_done_manager"):
                        yield stream._done_manager

                        for dm in Impl(stream._done_manager.stream):
                            yield dm

            # ----------------------------------------------------------------------
            
            yield self
            for dm in Impl(self.stream):
                yield dm


# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def InitAnsiSequenceStreams():
    return __InitAnsiSequenceStreamsImpl()

# ----------------------------------------------------------------------
def GenerateAnsiSequenceStream( stream, 
                                preserve_ansi_escape_sequences=False,
                                autoreset=False,
                                do_not_modify_std_streams=False,
                              ):
    return __GenerateAnsiSequenceStreamImpl( stream,
                                             preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                                             autoreset=autoreset,
                                             do_not_modify_std_streams=do_not_modify_std_streams,
                                           )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
__InitAnsiSequenceStreamsImpl_initialized   = ModifiableValue(False)

def __InitAnsiSequenceStreamsImpl():
    if not __InitAnsiSequenceStreamsImpl_initialized.value:
        import colorama

        colorama.init()
        __InitAnsiSequenceStreamsImpl_initialized.value = True

# ----------------------------------------------------------------------
@contextmanager
def __GenerateAnsiSequenceStreamImpl( stream, 
                                      preserve_ansi_escape_sequences=False,
                                      autoreset=False,
                                      do_not_modify_std_streams=False,
                                    ):
    # When colorama was initialized, sys.stdout and sys.stderr were
    # configured to strip and convert ansi escape sequences. However,
    # we may want to preserve those sequences. Assume that the stream 
    # ultimately resolves to sys.stdout and/or sys.stderr when
    # preserve_ansi_escape_sequence is True.
    if not preserve_ansi_escape_sequences:
        if not isinstance(stream, StreamDecorator):
            stream = StreamDecorator(stream)

        yield stream
        return

    import colorama.initialise as cinit
    from colorama.ansitowin32 import AnsiToWin32

    from CommonEnvironment.CallOnExit import CallOnExit

    restore_functors = []

    if do_not_modify_std_streams:
        restore_functors.append(lambda: None) # Necessary because CallOnExit requires at least one functor
    else:
        # ----------------------------------------------------------------------
        def RestoreConvertor(wrapped_stream, original_convertor):
            wrapped_stream._StreamWrapper__convertor = original_convertor

        # ----------------------------------------------------------------------

        for wrapped_stream, original_stream in [ ( cinit.wrapped_stdout, cinit.orig_stdout ),
                                                 ( cinit.wrapped_stderr, cinit.orig_stderr ),
                                               ]:
            original_convertor = wrapped_stream._StreamWrapper__convertor

            if not getattr(original_convertor, "_modified", False):
                convertor = AnsiToWin32( original_stream,
                                         strip=False,
                                         convert=False,
                                         autoreset=autoreset,
                                       )

                convertor._modified = True

                wrapped_stream._StreamWrapper__convertor = convertor
            
                restore_functors.append(lambda wrapped_stream=wrapped_stream, original_convertor=original_convertor: RestoreConvertor(wrapped_stream, original_convertor))

        if restore_functors:
            cinit.reinit()
            restore_functors.append(cinit.reinit)
        
    with CallOnExit(*restore_functors):
        this_stream = None

        wrapped = getattr(stream, "_StreamWrapper__wrapped")
        if wrapped:
            if wrapped == cinit.orig_stdout:
                this_stream = cinit.wrapped_stdout
            elif wrapped == cinit.orig_stderr:
                this_stream = cinit.wrapped_stderr
        
        if this_stream == None:
            this_stream = stream

        yield StreamDecorator(cinit.wrap_stream( this_stream,
                                                 convert=False,
                                                 strip=False,
                                                 autoreset=autoreset,
                                                 wrap=True,
                                               ))
                    