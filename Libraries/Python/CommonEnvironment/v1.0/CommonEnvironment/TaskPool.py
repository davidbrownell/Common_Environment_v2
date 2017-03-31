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
             output_stream=sys.stdout,
             verbose=False,
             silent=False,
             progress_bar=False,
             raise_on_error=False,
             display_exception_callstack=True,
           ):
    assert tasks

    tasks = [ _InternalTask(task) for task in tasks ]

    StatusUpdate = Enum.Create( "Start",
                                "Status",
                                "Stop",
                              )

    num_concurrent_tasks = num_concurrent_tasks or (multiprocessing.cpu_count() * 5)
    output_stream = StreamDecorator(None if silent else output_stream)

    # ----------------------------------------------------------------------
    def Invoke( on_initialized_functor,                 # def Func(futures, tasks)
                update_status_functor,                  # def Func(futures, tasks, future, task, update_type, optional_content)
                output_stream, 
                clear_status_when_complete=False,
              ):
        on_initialized_functor = on_initialized_functor or (lambda futures: None)

        tls = threading.local()
    
        thread_index = ModifiableValue(0)
        thread_index_mutex = threading.Lock()

        futures = []
        
        initialized = threading.Event()

        # ----------------------------------------------------------------------
        def Func(task, task_index):
            this_thread_index = getattr(tls, "index", None)
            if this_thread_index == None:
                with thread_index_mutex:
                    this_thread_index = thread_index.value
                    thread_index.value += 1
                    
                setattr(tls, "index", this_thread_index)

            initialized.wait()
            
            start_time = time.time()
            future = futures[task_index]

            sink = StringIO()
            
            # ----------------------------------------------------------------------
            def OnStatusUpdate(content):
                update_status_functor(futures, tasks, future, task, StatusUpdate.Status, content)
            
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
                update_status_functor(futures, tasks, future, task, StatusUpdate.Start, None)
                future.add_done_callback(lambda ignore, future=future, task=task: update_status_functor(futures, tasks, future, task, StatusUpdate.Stop, None))

            on_initialized_functor(futures, tasks)
            initialized.set()
            
            # Check for exceptions
            for future in futures:
                future.result()
            
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
            output_stream.write('\n'.join([ "\r{}".format(status) for status in statuses ]))    # Write the content...
            output_stream.write("\033[{}A\r".format(len(statuses) - 1))                         # Move back to the original line
        
        prev_statuses[:] = original_statuses

    # ---------------------------------------------------------------------------
    def UpdateStatuses(futures, tasks, write_functor=WriteStatuses):
        statuses = []

        for task in tasks:
            with task.status_lock:
                if task.status:
                    statuses.append(task.status)

        write_functor(statuses)

    # ----------------------------------------------------------------------
    
    output_lock = threading.Lock()

    if progress_bar:
        with tqdm( total=len(tasks),
                   file=output_stream,
                   ncols=None,
                   dynamic_ncols=True,
                   unit=" items",
                 ) as progress_bar:
            # ----------------------------------------------------------------------
            def PBWriteStatuses(*args, **kwargs):
                output_stream.write("\033[1B") # Move down one line to compensate for the progress bar
                WriteStatuses(*args, **kwargs)
                output_stream.write("\033[1A\r") # Move up one line to compensate for the progress bar

            # ----------------------------------------------------------------------
            def PBUpdateStatuses(futures, tasks):
                UpdateStatuses(futures, tasks, PBWriteStatuses)

            # ---------------------------------------------------------------------------
            def UpdateStatus(futures, tasks, future, task, update_type, optional_content):
                with task.status_lock:
                    task.status = optional_content if not optional_content else "    {}: {}".format(task.Name, optional_content)

                if update_type in [ StatusUpdate.Status, StatusUpdate.Stop, ]:
                    with output_lock:
                        if update_type == StatusUpdate.Stop:
                            progress_bar.update()

                        PBUpdateStatuses(futures, tasks)

            # ----------------------------------------------------------------------
            def OnInit(futures, tasks):
                PBUpdateStatuses(futures, tasks)

            # ----------------------------------------------------------------------
            
            with CallOnExit(lambda: PBWriteStatuses([])):
                return Invoke( OnInit,
                               UpdateStatus,
                               output_stream, 
                               clear_status_when_complete=True,
                             )
    else:
        
        # ----------------------------------------------------------------------
        def UpdateStatus(futures, tasks, future, task, update_type, optional_content):
            if task.complete.is_set():
                suffix = "DONE! ({}, {})".format(task.result, task.time_delta_string)
            elif future.running():
                suffix = "Running"
            else:
                suffix = "Queued"

            if optional_content:
                suffix += " [{}]".format(optional_content)

            with task.status_lock:
                task.status = "  {name:<70} {suffix}".format( name="{}:".format(task.Name),
                                                              suffix=suffix,
                                                            )

            if update_type in [ StatusUpdate.Status, StatusUpdate.Stop, ]:
                UpdateStatuses(futures, tasks)
                
        # ----------------------------------------------------------------------
        def OnInit(futures, tasks):
            UpdateStatuses(futures, tasks)

        # ----------------------------------------------------------------------
        
        with CallOnExit(lambda: WriteStatuses([])):
            return Invoke( OnInit,
                           UpdateStatus,
                           output_stream,
                         )
        
# ----------------------------------------------------------------------
def Transform( items, 
               functor,                                                     # def Func(item) -> transformed item
               optional_output_stream,                                      # Will display a progress bar if not None
               display_exception_callstack=False,
               num_concurrent_tasks=multiprocessing.cpu_count(),
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
    def Impl(task_index, on_status_functor):
        transformed_items[task_index] = functor(OrderedDict([ ( "item", items[task_index] ),
                                                              ( "on_status_functor", on_status_functor ),
                                                            ]))

    # ----------------------------------------------------------------------
    
    Execute( [ Task( name_functor(index, item),
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
