# ---------------------------------------------------------------------------
# |  
# |  TaskPool.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/05/2015 09:50:45 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import multiprocessing
import os
import sys
import threading
import textwrap
import time
import traceback

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, wait

import six
from six.moves import StringIO

from tqdm import tqdm

from CommonEnvironment import ModifiableValue
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Enum
from CommonEnvironment import Interface
from CommonEnvironment import Package
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Task(object):
    def __init__( self,
                  name,                     # "Foo"
                  action_description,       # "Building Foo"
                  functor,                  # def Functor(<args>) -> None or str or (result, str)
                                            #
                                            #       Where <args> can be zero or more of the following:
                                            #           task_index
                                            #           core_index          # Technically speaking, this isn't the core index but can be used to simulate thread local storage
                                            #           output_stream
                ):
        assert name
        assert action_description
        assert functor

        self.Name                           = name
        self.ActionDescription              = action_description
        self.Functor                        = Interface.CreateCulledCallable(functor)

        # Working data
        self.output                         = ''
        self.result                         = 0
        self.time_delta_string              = ''

        self.status                         = None
        self.status_lock                    = threading.Lock()

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def ExecuteEx( tasks,
               num_concurrent_tasks=None,
               output_stream=sys.stdout,
               verbose=False,
               silent=False,
               progress_bar=False,
               raise_on_error=False,
               display_exception_callstack=True,
             ):
    assert tasks

    StatusUpdate = Enum.Create( "Enter",
                                "Status",
                                "Exit",
                              )

    num_concurrent_tasks = num_concurrent_tasks or (multiprocessing.cpu_count() * 5)
    output_stream = StreamDecorator(None if silent else output_stream)

    tls = threading.local()
    
    thread_index = ModifiableValue(0)
    thread_index_mutex = threading.Lock()

    prev_statuses = []

    # ----------------------------------------------------------------------
    def Invoke(update_functor, output_stream):
        futures = []
        initialized = threading.Event()
        
        # ----------------------------------------------------------------------
        def Func(update_functor, task, task_index):
            index = getattr(tls, "index", None)
            if index == None:
                with thread_index_mutex:
                    index = thread_index.value
                    thread_index.value += 1
                    
                setattr(tls, "index", index)
                
            initialized.wait()
            
            update_functor(thread_index, futures, task, StatusUpdate.Enter)
            with CallOnExit(lambda: update_functor(thread_index, futures, task, StatusUpdate.Exit)):
                start_time = time.time()
                sink = StringIO()
                
                # ----------------------------------------------------------------------
                def OnStatusUpdate(content):
                    with task.status_lock:
                        task.status = content

                    update_functor(thread_index, futures, task, StatusUpdate.Status)

                # ----------------------------------------------------------------------
                
                try:
                    result = task.Functor(OrderedDict([ ( "task_index", task_index ),
                                                        ( "output_stream", sink ),
                                                        ( "core_index", thread_index ),
                                                        ( "on_status_update", OnStatusUpdate ),
                                                      ]))
                    if result == None:
                        task.result = 0

                    elif isinstance(result, six.string_types):
                        task.result = 0
                        sink.write(result)

                    elif isinstance(result, tuple):
                        task.result = result[0]
                        sink.write(result[1])

                    else:
                        task.result = result

                except:
                    task.result = -1

                    message = str(sys.exc_info()[1]).rstrip()
                    
                    OnStatusUpdate("ERROR: {}".format(message))
                    
                    if display_exception_callstack:
                        sink.write(traceback.format_exc())
                    else:
                        sink.write("{}\n".format(message))

                task.output = sink.getvalue()
                task.time_delta_string = str(datetime.timedelta(seconds=(time.time() - start_time)))

        # ----------------------------------------------------------------------
        
        with ThreadPoolExecutor(num_concurrent_tasks) as executor:
            futures = [ executor.submit(Func, update_functor, task, index) for index, task in enumerate(tasks) ]
            initialized.set()
            
            wait(futures)
            
        # Calculate the final result
        sink = StringIO()

        # ----------------------------------------------------------------------
        def Output(stream, task):
            stream.write(textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # |  
                # |  {name} ({result}, {time})
                # |  
                # ----------------------------------------------------------------------
                {output}

                """).format( name=task.Name,
                             result=task.result,
                             time=task.time_delta_string,
                             output=task.output,
                           ))

        # ----------------------------------------------------------------------
        
        result = 0

        for task in tasks:
            if task.result != 0:
                Output(sink, task)
                result = result or task.result

        sink = sink.getvalue()
        if result != 0:
            if raise_on_error:
                raise Exception(sink or result)
            else:
                output_stream.write(sink)

        if verbose and result == 0:
            for task in tasks:
                if task.output:
                    Output(output_stream, task)

        return result

    # ----------------------------------------------------------------------
    def WriteStatuses(output_stream, statuses):
        original_statuses = list(statuses)

        for index, status in enumerate(statuses):
            if index < len(prev_statuses):
                prev_status = prev_statuses[index]
            else:
                prev_status = ''

            if len(status) < len(prev_status):
                statuses[index] = "{}{}".format(status, ' ' * (len(prev_status) - len(status)))

        if len(statuses) < len(prev_statuses):
            for index in six.moves.range(len(statuses), len(prev_statuses)):
                statuses.append(' ' * len(prev_statuses[index]))

        if statuses:
            output_stream.write('\n'.join([ "\r{}".format(status) for status in statuses ]))    # Write the content...
            output_stream.write("\033[{}A\r".format(len(statuses) - 1))                         # Move back to the original line
        
        prev_statuses[:] = original_statuses

    # ---------------------------------------------------------------------------
            
    if progress_bar:
        with tqdm( total=len(tasks),
          file=output_stream,
          ncols=None,
          dynamic_ncols=True,
          unit=" items",
        ) as progress_bar:
            progress_bar_lock = threading.Lock()

            # ----------------------------------------------------------------------
            def PBWriteStatuses(*args, **kwargs):
                output_stream.write("\033[1B") # Move down one line to compensate for the progress bar
                WriteStatuses(*args, **kwargs)
                output_stream.write("\033[1A\r") # Move up one line to compensate for the progress bar

            # ----------------------------------------------------------------------
            def ProgressBarUpdate(thread_index, futures, task, update_type):
                with progress_bar_lock:
                    if update_type == StatusUpdate.Exit:
                        progress_bar.update()
                    
                    statuses = []

                    for task in tasks:
                        with task.status_lock:
                            if task.status:
                                statuses.append("    {}: {}".format(task.Name, task.status))

                    PBWriteStatuses(output_stream, statuses)
                    
            # ---------------------------------------------------------------------------

            with CallOnExit(lambda: PBWriteStatuses(output_stream, [])):
                return Invoke(ProgressBarUpdate, output_stream)
    else:
        with output_stream.DoneManager( line_prefix='',
                                        done_prefix="Task pool ",
                                      ) as si:
            output_lock = threading.Lock()

            # ----------------------------------------------------------------------
            def Update(thread_index, futures, task, update_type):
                statuses = []

                for future, task in six.moves.zip(futures, tasks):
                    if future.running():
                        status = "Running"
                    elif future.done():
                        status = "DONE! ({}, {})".format(task.result, task.time_delta_string)
                    else:
                        status = "Queued"

                    detail = ''
                    with task.status_lock:
                        if task.status:
                            detail = " [{}]".format(task.status)

                    statuses.append("{name:<70} {status}{detail}".format( name="{}:".format(task.Name),
                                                                          status=status,
                                                                          detail=detail,
                                                                        ))

                with output_lock:
                    WriteStatuses(si.stream, statuses)

            # ----------------------------------------------------------------------
            
            with CallOnExit(lambda: WriteStatuses(si.stream, [])):
                return Invoke(Update, si.stream)

# ----------------------------------------------------------------------
def Execute( tasks,
             num_concurrent_tasks=multiprocessing.cpu_count(),
             output_stream=sys.stdout,
             verbose=False,
             silent=False,
             progress_bar=False,
             raise_on_error=False,
             display_exception_callstack=True,
           ):
    assert tasks
    assert num_concurrent_tasks

    num_concurrent_tasks = min(num_concurrent_tasks, len(tasks))
    output_stream = StreamDecorator(None if silent else output_stream)
    
    # ---------------------------------------------------------------------------
    class Executor(object):
        # ---------------------------------------------------------------------------
        def __init__( self,
                      num_tasks,
                      is_multithreaded,
                    ):
            self._done_lock                 = threading.Lock()

            self._num_invocations           = 0
            self._ticks                     = 0

            self._remaining                 = num_tasks
            self._num_tasks                 = num_tasks
            self._is_multithreaded          = is_multithreaded

        # ---------------------------------------------------------------------------
        @property
        def NumTasks(self):
            return self._num_tasks

        # ---------------------------------------------------------------------------
        def Execute( self,
                     task,
                     core_index,
                     task_index,
                     output_stream,
                   ):
            assert task
            assert output_stream

            start_time = time.time()
            
            # ---------------------------------------------------------------------------
            def GeneratePrefix():
                return "[{index:<{adjust}} of {total}]: ".format( adjust=len(str(self._num_tasks)),
                                                                  index=task_index + 1,
                                                                  total=self._num_tasks,
                                                                )

            # ---------------------------------------------------------------------------
            def DoneStatement():
                with self._done_lock:
                    # Get the num remaining
                    self._remaining -= 1
                    remaining = self._remaining

                    # Get the num of invocations
                    self._num_invocations += 1
                    num_invocations = self._num_invocations

                    # Get the time remaining
                    self._ticks += (time.time() - start_time)
                    ticks = self._ticks

                # ---------------------------------------------------------------------------
                def TimeEstimate(modifier):
                    return str(datetime.timedelta(seconds=(((float(ticks) / num_invocations) * modifier) / num_concurrent_tasks)))

                # ---------------------------------------------------------------------------
                
                output_stream.write("{prefix}DONE! ({result:<4} {time:>16}) [{remaining} left, ETA ~{eta}, Total ~{total}]\n".format( prefix=GeneratePrefix() if self._is_multithreaded else '',
                                                                                                                                      result="{},".format(task.result),
                                                                                                                                      time=task.time_delta_string,
                                                                                                                                      remaining=remaining,
                                                                                                                                      eta=TimeEstimate(remaining),
                                                                                                                                      total=TimeEstimate(self._num_tasks),
                                                                                                                                    ))

            # ---------------------------------------------------------------------------
            
            output_stream.write("{0:<107}".format("{}{}...".format(GeneratePrefix(), task.ActionDescription)))
            with CallOnExit(DoneStatement):
                sink = StringIO()

                try:
                    result = task.Functor(OrderedDict([ ( "task_index", task_index ), 
                                                        ( "output_stream", sink ),
                                                        ( "core_index", core_index ),
                                                      ]))
                    if result == None:
                        task.result = 0

                    elif isinstance(result, str):
                        task.result = 0
                        sink.write(result)

                    elif isinstance(result, tuple):
                        task.result = result[0]
                        sink.write(result[1])

                    else:
                        task.result = result

                except:
                    task.result = -1

                    if display_exception_callstack:
                        sink.write(traceback.format_exc())
                    else:
                        ex = sys.exc_info()[1]
                        sink.write("{}\n".format(str(ex).rstrip()))

                task.output = sink.getvalue()
                task.time_delta_string = str(datetime.timedelta(seconds=(time.time() - start_time)))

    # ---------------------------------------------------------------------------
    class ThreadSafeStreamDecorator(object):
        # ---------------------------------------------------------------------------
        def __init__( self,
                      thread_info,
                      core_index,
                      num_cores,
                      task_index,
                    ):
            self._thread_info               = thread_info
            self._core_index                = core_index
            self._num_cores                 = num_cores
            self._task_index                = task_index

        # ---------------------------------------------------------------------------
        def write(self, content):
            with self._thread_info.output_lock:
                output_stream.write("[Core {0:>{1}}] {2}".format( self._core_index, 
                                                                  len(str(self._num_cores - 1)),
                                                                  content,
                                                                ))

                if content and content[-1] != '\n':
                    output_stream.write("\n")

        # ---------------------------------------------------------------------------
        def flush(self):
            with self._thread_info.output_lock:
                output_stream.flush()

    # ---------------------------------------------------------------------------
    def InternalThreadProc(thread_info, core_index):
        while True:
            with thread_info.index_lock:
                if thread_info.current_index == thread_info.executor.NumTasks:
                    return
            
                task_index = thread_info.current_index
                thread_info.current_index += 1
            
            with CallOnExit(thread_info.progress_bar_update_func):
                thread_info.executor.Execute( thread_info.tasks[task_index],
                                              core_index,
                                              task_index,
                                              StreamDecorator(None) if progress_bar else ThreadSafeStreamDecorator( thread_info, 
                                                                                                                    core_index, 
                                                                                                                    num_concurrent_tasks,
                                                                                                                    task_index,
                                                                                                                  ),
                                            )

    # ---------------------------------------------------------------------------
    def Invoke(update_functor, output_stream):
        executor = Executor(len(tasks), num_concurrent_tasks != 1)

        if num_concurrent_tasks == 1:
            status_output_stream = StreamDecorator(None) if progress_bar else output_stream

            for index, task in enumerate(tasks):
                executor.Execute(task, 0, index, status_output_stream)
                update_functor()
        else:
            thread_info = QuickObject( executor=executor,
        
                                       current_index=0,
        
                                       index_lock=threading.Lock(),
                                       output_lock=threading.Lock(),
                                       progress_bar_update_func=update_functor,
                                       
                                       tasks=tasks,
                                       output_stream=output_stream,
                                     )
        
            # Create the threads
            threads = []
        
            while True:
                if len(threads) == num_concurrent_tasks:
                    break
        
                # ---------------------------------------------------------------------------
                def ThreadProc(index=len(threads)): 
                    InternalThreadProc(thread_info, index)
        
                # ---------------------------------------------------------------------------
                
                threads.append(threading.Thread(target=ThreadProc))
                threads[-1].start()
        
            # Wait for all threads to complete
            for thread in threads:
                thread.join()

        # Calculate the final result

        sink = StringIO()

        # ----------------------------------------------------------------------
        def Output(stream, task):
            stream.write(textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # |  
                # |  {name} ({result}, {time})
                # |  
                # ----------------------------------------------------------------------
                {output}

                """).format( name=task.Name,
                             result=task.result,
                             time=task.time_delta_string,
                             output=task.output,
                           ))

        # ----------------------------------------------------------------------
        
        result = 0

        for task in tasks:
            if task.result != 0:
                Output(sink, task)
                result = result or task.result

        sink = sink.getvalue()
        if result != 0:
            if raise_on_error:
                raise Exception(sink or result)
            else:
                output_stream.write(sink)

        if verbose and result == 0:
            for task in tasks:
                if task.output:
                    Output(output_stream, task)

        return result

    # ----------------------------------------------------------------------
    
    if progress_bar:
        with tqdm( total=len(tasks),
                   file=output_stream,
                   ncols=None,
                   dynamic_ncols=True,
                   unit=" items",
                 ) as progress_bar:
            progress_bar_lock = threading.Lock()

            # ---------------------------------------------------------------------------
            def ProgressBarUpdate():
                with progress_bar_lock:
                    progress_bar.update()
                    
            # ---------------------------------------------------------------------------

            return Invoke(ProgressBarUpdate, output_stream)
    else:
        with output_stream.DoneManager( line_prefix='',
                                        done_prefix="\nTask pool ",
                                      ) as si:
            return Invoke(lambda: None, si.stream)
        
# ----------------------------------------------------------------------
def Transform( items, 
               functor,                     # def Func(item) -> transformed item
               optional_output_stream,      # Will display a progress bar if not None
               display_exception_callstack=False,
               num_concurrent_tasks=multiprocessing.cpu_count(),
             ):
    """\
    Applies the functor to each item in the item list, returning a list of 
    the transformed items. The operation is considered to be atomic, and will
    raise an exception if one or more of the functor invocations fail.
    """
    assert items
    assert functor

    transformed_items = [ None, ] * len(items)

    # ----------------------------------------------------------------------
    def Impl(task_index):
        transformed_items[task_index] = functor(items[task_index])

    # ----------------------------------------------------------------------
    
    Execute( [ Task( "Results from Index {} ({})".format(index, str(item)),
                     str(index),
                     Impl,
                   )
               for index, item in enumerate(items)
             ],
             output_stream=optional_output_stream if bool(optional_output_stream) else StreamDecorator(None),
             progress_bar=bool(optional_output_stream),
             raise_on_error=True,
             display_exception_callstack=display_exception_callstack,
             num_concurrent_tasks=num_concurrent_tasks,
           )

    return transformed_items
