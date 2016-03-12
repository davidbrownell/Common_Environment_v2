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
# |  Copyright David Brownell 2015-16.
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
from StringIO import StringIO

from TimeDelta import TimeDelta

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class StreamDecorator(object):
    """\
    Decorates the provided stream.
    """

    _eol_regex = re.compile(r"(?P<eol>\r?\n)")

    # ---------------------------------------------------------------------------
    def __init__( self,
                  stream_or_streams,
                  line_prefix='',
                  line_suffix='',           # string or def Func(column) -> string
                  prefix='',
                  suffix='',
                  one_time_prefix='',
                  one_time_suffix='',
                  tab_length=4,
                  skip_first_line_prefix=False,
                ):
        self._streams                       = stream_or_streams if isinstance(stream_or_streams, list) else [ stream_or_streams, ] if stream_or_streams != None else []
        self._line_prefix                   = line_prefix
        self._line_suffix                   = line_suffix
        self._prefix                        = prefix
        self._suffix                        = suffix
        self._one_time_prefix               = one_time_prefix
        self._one_time_suffix               = one_time_suffix
        self._tab_length                    = tab_length

        self._displayed_one_time_prefix     = False
        self._displayed_one_time_suffix     = False
        self._displayed_prefix              = False
        self._skip_first_line_prefix        = skip_first_line_prefix

        self._column                        = 0

    # ---------------------------------------------------------------------------
    @property
    def IsSet(self):
        return bool(self._streams)

    # ---------------------------------------------------------------------------
    def write(self, content, custom_line_prefix=''):
        if not self._streams or not content:
            return self

        # ---------------------------------------------------------------------------
        def WriteRaw(content):
            for stream in self._streams:
                stream.write(content)

        # ---------------------------------------------------------------------------
        def Impl(content, eol=None):
            if self._column == 0:
                if self._skip_first_line_prefix:
                    self._skip_first_line_prefix = False
                else:
                    WriteRaw(self._line_prefix)

                    if custom_line_prefix:
                        WriteRaw(custom_line_prefix)

            WriteRaw(content)
            self._column += len(content) + (content.count('\t') * (self._tab_length - 1))

            if eol:
                WriteRaw(self._line_suffix)
                WriteRaw(eol)

                self._column = 0

        # ---------------------------------------------------------------------------
        
        if not self._displayed_one_time_prefix:
            WriteRaw(self._one_time_prefix)
            self._displayed_one_time_prefix = True

        if not self._displayed_prefix:
            WriteRaw(self._prefix)
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
            suffix = self._line_suffix(self._column) if callable(self._line_suffix) else self._line_suffix

            for stream in self._streams:
                stream.write(suffix)
                stream.write(self._suffix)

            self._column = 0
            self._displayed_prefix = False
        
        if not self._displayed_one_time_suffix:
            for stream in self._streams:
                stream.write(self._one_time_suffix)

            self._displayed_one_time_suffix = True

        return self

    # ----------------------------------------------------------------------
    @contextmanager
    def DoneManagerEx( self,
                       
                       line_prefix="  ",

                       done_prefix='',
                       done_suffix='',
                       done_suffix_functor=None,        # Can be functor or list, def Func() -> string
                       done_result=True,
                       done_time=True,

                       display_exceptions=True,
                       display_exception_callstack=True,
                       suppress_exceptions=False,
                     ):
        done_suffix_functors = done_suffix_functor if isinstance(done_suffix_functor, list) else [ done_suffix_functor, ]

        start_time = TimeDelta()

        # ----------------------------------------------------------------------
        class Info(object):
            def __init__(self, stream, result=0):
                self.stream                 = stream
                self.result                 = result

                self.stream._parent_info = self

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

            if suffixes:
                content = ', '.join(suffixes)

                if done_prefix.strip():
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
                            .format( prefix=done_prefix,
                                     content=content,
                                     suffix=done_suffix,
                                   ))
            self.flush()

            # Propagate the result
            if info.result != 0:
                stream = self

                while hasattr(stream, "_parent_info"):
                    if stream._parent_info.result != 0:
                        break

                    stream._parent_info.result = info.result
                    stream = stream._parent_info.stream

        # ----------------------------------------------------------------------
        
        from .CallOnExit import CallOnExit

        with CallOnExit(Cleanup):
            try:
                yield info

                if info.result == None:
                    info.result = 0

            except Exception, ex:
                if info.result == None or info.result == 0:
                    info.result = -1

                if display_exceptions:
                    if display_exception_callstack:
                        import traceback
                        info.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify(traceback.format_exc(), len("ERROR: ")).rstrip()))
                    else:
                        info.stream.write("ERROR: {}\n".format(str(ex).rstrip()))

                if not suppress_exceptions:
                    raise ex

    # ---------------------------------------------------------------------------
    @contextmanager
    def DoneManager( self, 
                     show_rval=True,
                     show_time=True,
                     suffix_functor=None,      # def Func() -> string
                     display_callstack_on_error=True,
                     line_prefix="  ",
                     done_prefix='',
                     done_suffix='',
                     suppress_exceptions=False,
                     display_exceptions=True,
                   ):
        start_time = TimeDelta()

        # We are dynamically introducing the '_parent_info' attribute, so disable assocaited warnings
        # pylint: disable = W0212
        # pylint: disable = E1101

        # ---------------------------------------------------------------------------
        class Info(object):
            def __init__(self, stream, result=0):
                self.stream = stream
                self.result = result

                self.stream._parent_info = self

        # ---------------------------------------------------------------------------
        
        info = Info(StreamDecorator( self, 
                                     one_time_prefix='\n' if line_prefix else '', 
                                     line_prefix=line_prefix,
                                   ))
        
        # ---------------------------------------------------------------------------
        def Cleanup():
            if info.result == None:
                info.result = 0

            suffixes = []

            if show_rval:
                suffixes.append(str(info.result))
    
            if show_time:
                suffixes.append(start_time.CalculateDelta(as_string=True))
    
            if suffix_functor:
                result = suffix_functor()
                if result != None:
                    suffixes.append(result)
    
            self.write("{prefix}{done}{info_suffix}{suffix}\n".format( prefix=done_prefix, 
                                                                       done='' if done_prefix else "DONE!",
                                                                       info_suffix=" ({})".format(', '.join(suffixes)) if suffixes else '',
                                                                       suffix=done_suffix,
                                                                     ))
            self.flush()
    
            # Propagate the result
            if info.result != 0:
                stream = self
                
                while hasattr(stream, "_parent_info"):
                    if stream._parent_info.result != 0:
                        break
    
                    stream._parent_info.result = info.result
                    stream = stream._parent_info.stream
    
        # ---------------------------------------------------------------------------
        
        from .CallOnExit import CallOnExit

        with CallOnExit(Cleanup):
            try:
                yield info

                if info.result == None:
                    info.result = 0

            except Exception, ex:
                if info.result == None or info.result == 0:
                    info.result = -1

                if display_exceptions:
                    if display_callstack_on_error:
                        import traceback
                        info.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify(traceback.format_exc(), len("ERROR: ")).rstrip()))
                    else:
                        info.stream.write("ERROR: {}\n".format(str(ex).rstrip()))

                if not suppress_exceptions:
                    raise ex
                
    # ---------------------------------------------------------------------------
    @classmethod
    def LeftJustify(cls, content, starting_col=4, skip_first_line=True):
        whitespace_prefix = ' ' * starting_col
        
        sink = StringIO()
        decorator = cls( sink, 
                         line_prefix=whitespace_prefix, 
                         skip_first_line_prefix=skip_first_line,
                       )

        decorator.write(content)
        decorator.flush()

        return sink.getvalue()

    # ---------------------------------------------------------------------------
    @classmethod
    def Wrap(cls, content, cols=80):
        if not content:
            return ''

        content = '\n'.join([ line.strip() for line in content.split('\n') ])
        paragraphs = [ textwrap.fill(paragraph, cols) for paragraph in content.split('\n\n') ]

        return '\n\n'.join(paragraphs)
        