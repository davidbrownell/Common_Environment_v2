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
from concurrent.futures import ThreadPoolExecutor
import six
from six.moves import StringIO

from CommonEnvironment import ModifiableValue
from CommonEnvironment import Enum
from CommonEnvironment import Interface
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

StreamDecorator.InitAnsiSequenceStreams()

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
                                            #           on_status_functor   # def Func(content)
                ):
        assert name
        assert action_description
        assert functor

        self.Name                           = name
        self.ActionDescription              = action_description
        self.Functor                        = functor

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def Execute( tasks,
             num_concurrent_tasks=None,
             output_stream=sys.stdout,      # optional
             verbose=False,
             progress_bar=False,
             progress_bar_cols=120,
             raise_on_error=False,
             display_exception_callstack=True,
             display_errors=True,
           ):
    assert tasks

    tasks = [ _InternalTask(task) for task in tasks ]
    num_concurrent_tasks = num_concurrent_tasks or (multiprocessing.cpu_count() * 5)
    output_stream = output_stream or StreamDecorator(None)

    # ----------------------------------------------------------------------
    StatusUpdate = Enum.Create( "Start",
                                "Status",
                                "Stop",
                              )

    # ----------------------------------------------------------------------
    def Invoke( get_status_functor,                     # def Func(future, task, update_type, optional_content) -> string
                write_statuses_functor,                 # def Func(statuses)
                clear_status_when_complete=False,
                display_status_update_frequency=0.5,   # seconds
              ):
        tls = threading.local()
    
        thread_index = ModifiableValue(0)
        thread_index_mutex = threading.Lock()

        futures = []
        
        initialized_event = threading.Event()
        terminate_event = threading.Event()

        # ----------------------------------------------------------------------
        def UpdateStatus(future, task, update_type, optional_content):
            with task.status_lock:
                task.status = get_status_functor(future, task, update_type, optional_content)

        # ----------------------------------------------------------------------
        def DisplayStatusesThreadProc():
            prev_statuses = None

            while True:
                statuses = []

                for task in tasks:
                    with task.status_lock:
                        if task.status:
                            statuses.append(task.status)

                if statuses != prev_statuses:
                    write_statuses_functor(statuses)
                    prev_statuses = statuses
                
                initialized_event.set()

                if terminate_event.wait(display_status_update_frequency):
                    break

            write_statuses_functor([])

        # ----------------------------------------------------------------------
        def Func(task, task_index):
            this_thread_index = getattr(tls, "index", None)
            if this_thread_index == None:
                with thread_index_mutex:
                    this_thread_index = thread_index.value
                    thread_index.value += 1
                    
                setattr(tls, "index", this_thread_index)

            initialized_event.wait()
            
            start_time = time.time()
            future = futures[task_index]

            sink = StringIO()
            
            # ----------------------------------------------------------------------
            def OnStatusUpdate(content):
                UpdateStatus(future, task, StatusUpdate.Status, content)
                
            # ----------------------------------------------------------------------
            
            try:
                result = task.Functor(OrderedDict([ ( "task_index", task_index ),
                                                    ( "output_stream", sink ),
                                                    ( "core_index", this_thread_index ),
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
            
            if clear_status_when_complete:
                OnStatusUpdate(None)
            
            task.output = sink.getvalue()
            task.time_delta_string = str(datetime.timedelta(seconds=(time.time() - start_time)))

            task.complete.set()

        # ----------------------------------------------------------------------
        
        with ThreadPoolExecutor(num_concurrent_tasks) as executor:
            futures += [ executor.submit(Func, task, index) for index, task in enumerate(tasks) ]

            # We can't combine this loop with the comprehension above, as the
            # update status functor expects a full set of futures.
            for future, task in six.moves.zip(futures, tasks):
                UpdateStatus(future, task, StatusUpdate.Start, None)
                future.add_done_callback(lambda ignore, future=future, task=task: UpdateStatus(future, task, StatusUpdate.Stop, None))

            display_thread = threading.Thread(target=DisplayStatusesThreadProc)
            display_thread.start()

            # Check for exceptions
            for future in futures:
                future.result()

            terminate_event.set()
            display_thread.join()

    # ----------------------------------------------------------------------
    prev_statuses = []

    def WriteStatuses(statuses):
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
            output_stream.write('\n'.join([ "\r{}".format(status) for status in statuses ]))    # Write the content
            output_stream.write("\033[{}A\r".format(len(statuses) - 1))                         # Move back to the original line
        
        prev_statuses[:] = original_statuses

    # ----------------------------------------------------------------------
    
    if progress_bar:
        from tqdm import tqdm

        progress_bar_lock = threading.Lock()

        with tqdm( total=len(tasks),
                   file=output_stream,
                   ncols=progress_bar_cols,
                   unit=" items",
                 ) as progress_bar:
            # ----------------------------------------------------------------------
            def PBWriteStatuses(statuses):
                with progress_bar_lock:
                    output_stream.write("\033[1B") # Move down one line to compensate for the progress bar
                    WriteStatuses(statuses)
                    output_stream.write("\033[1A\r") # Move up one line to compensate for the progress bar

            # ---------------------------------------------------------------------------
            def GetStatus(future, task, update_type, optional_content):
                if update_type == StatusUpdate.Stop:
                    with progress_bar_lock:
                        progress_bar.update()

                if not optional_content:
                    return optional_content

                return "    {}: {}".format(task.Name, optional_content)

            # ----------------------------------------------------------------------
            
            Invoke( GetStatus,
                    PBWriteStatuses,
                    clear_status_when_complete=True,
                  )
    else:
        max_name_length = max(50, *[ len(task.Name) for task in tasks ])
        
        status_template = "  {{name:<{}}} {{suffix}}".format(max_name_length + 1)

        # ----------------------------------------------------------------------
        def GetStatus(future, task, update_type, optional_content):
            if task.complete.is_set():
                suffix = "DONE! ({}, {})".format(task.result, task.time_delta_string)
            elif future.running():
                suffix = "Running"
            else:
                suffix = "Queued"

            if optional_content:
                suffix += " [{}]".format(optional_content)

            return status_template.format( name="{}:".format(task.Name),
                                           suffix=suffix,
                                         )

        # ----------------------------------------------------------------------
        
        Invoke(GetStatus, WriteStatuses)

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

    if display_errors and result != 0:
        if raise_on_error:
            raise Exception(sink or result)
        elif hasattr(output_stream, "write_error"):
            for line in sink.split('\n'):
                output_stream.write_error(line)         # <Has no 'write_error' member> pylint: disable = E1101
        else:
            output_stream.write(sink)

    if verbose and result == 0:
        sink = StringIO()

        for task in tasks:
            if task.output:
                Output(sink, task)

        sink = sink.getvalue()

        if hasattr(output_stream, "write_verbose"):
            for line in sink.split('\n'):
                output_stream.write_verbose(line)       # <Has no 'write_verbose' member> pylint: disable = E1101
        else:
            output_stream.write(sink)

    return result
        
# ----------------------------------------------------------------------
def Transform( items, 
               functor,                                                     # def Func(item) -> transformed item
               optional_output_stream,                                      # Will display a progress bar if not None
               display_exception_callstack=False,
               display_errors=True,
               num_concurrent_tasks=None,
               name_functor=None,                                           # def Func(index, item) -> string
             ):
    """\
    Applies the functor to each item in the item list, returning a list of 
    the transformed items. The operation is considered to be atomic, and will
    raise an exception if one or more of the functor invocations fail.
    """
    assert items
    assert functor

    functor = Interface.CreateCulledCallable(functor)
    name_functor = name_functor or (lambda index, item: "Results from Index {} ({})".format(index, str(item)))

    transformed_items = [ None, ] * len(items)

    # ----------------------------------------------------------------------
    def Impl(task_index, on_status_update):
        transformed_items[task_index] = functor(OrderedDict([ ( "item", items[task_index] ),
                                                              ( "on_status_update", on_status_update ),
                                                            ]))

    # ----------------------------------------------------------------------
    
    Execute( [ Task( name_functor(index, item),
                     str(index),
                     Impl,
                   )
               for index, item in enumerate(items)
             ],
             output_stream=optional_output_stream,
             progress_bar=bool(optional_output_stream),
             raise_on_error=True,
             display_exception_callstack=display_exception_callstack,
             display_errors=display_errors,
             num_concurrent_tasks=num_concurrent_tasks,
           )

    return transformed_items

# ----------------------------------------------------------------------
# |  
# |  Internal Types
# |  
# ----------------------------------------------------------------------
class _InternalTask(Task):

    # ----------------------------------------------------------------------
    def __init__(self, task):
        super(_InternalTask, self).__init__(task.Name, task.ActionDescription, Interface.CreateCulledCallable(task.Functor))

        # Working data
        self.output                         = ''
        self.result                         = 0
        self.time_delta_string              = ''

        self.status                         = None
        self.status_lock                    = threading.Lock()

        self.complete                       = threading.Event()
