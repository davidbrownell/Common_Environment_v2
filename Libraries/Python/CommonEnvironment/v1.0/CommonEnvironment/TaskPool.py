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
# |  Copyright David Brownell 2015-16.
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

from StringIO import StringIO

from tqdm import tqdm

from CommonEnvironment.CallOnExit import CallOnExit
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

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def Execute( tasks,
             num_concurrent_tasks=multiprocessing.cpu_count(),
             output_stream=sys.stdout,
             verbose=False,
             silent=False,
             progress_bar=False,
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
                    result = task.Functor( core_index=core_index,
                                           task_index=task_index, 
                                           output_stream=sink,
                                         )

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
                    sink.write(traceback.format_exc())
                    task.result = -1

                task.output = sink.getvalue()
                task.time_delta_string = datetime.timedelta(seconds=(time.time() - start_time))

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
            with CallOnExit(thread_info.progress_bar_update_func):
                with thread_info.index_lock:
                    if thread_info.current_index == thread_info.executor.NumTasks:
                        return
                
                    task_index = thread_info.current_index
                    thread_info.current_index += 1
                
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
                Output(output_stream, task)
                result = result or task.result

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
        